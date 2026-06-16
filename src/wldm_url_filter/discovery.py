"""Candidate page discovery from validated source domains."""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

import httpx
from bs4 import BeautifulSoup
from bs4.element import Tag

from wldm_url_filter.config import (
    DEFAULT_SETTINGS,
    RuntimeSettings,
    UnsafeUrlError,
    normalize_target_url,
    normalized_url_key,
)
from wldm_url_filter.logging_config import log_runtime_diagnostic
from wldm_url_filter.models import (
    CandidatePage,
    DiscoveryScope,
    DiscoverySource,
    SourceDomain,
    TargetKeyword,
    ValidationStatus,
)

LOGGER = logging.getLogger(__name__)

UTILITY_PATH_PARTS = {
    "about",
    "account",
    "admin",
    "archive",
    "author",
    "cart",
    "category",
    "contact",
    "login",
    "privacy",
    "search",
    "signin",
    "signup",
    "tag",
    "terms",
}
CONTENT_HINTS = {
    "article",
    "blog",
    "case-study",
    "guide",
    "insight",
    "learn",
    "news",
    "post",
    "review",
    "resource",
    "story",
}


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    """Candidate pages and depth decisions for one discovery run."""

    candidates: list[CandidatePage]
    scopes: list[DiscoveryScope]
    diagnostics: list[str]


@dataclass(frozen=True, slots=True)
class FetchedPage:
    """Fetched HTML page details."""

    url: str
    html: str
    redirected: bool


def discover_candidate_pages(
    source_domains: Sequence[SourceDomain],
    target_keywords: Sequence[TargetKeyword],
    *,
    settings: RuntimeSettings = DEFAULT_SETTINGS,
    client: httpx.Client | None = None,
) -> DiscoveryResult:
    """Discover prioritized candidate pages for valid source domains."""
    candidates: list[CandidatePage] = []
    scopes: list[DiscoveryScope] = []
    diagnostics: list[str] = []
    owns_client = client is None
    active_client = client or httpx.Client(
        follow_redirects=True,
        timeout=settings.fast_pass_timeout_seconds,
    )

    try:
        for source_domain in source_domains:
            if source_domain.validation_status != ValidationStatus.VALID:
                diagnostic = log_runtime_diagnostic(
                    LOGGER,
                    logging.INFO,
                    "跳过无效或重复的源域名",
                    {"domain": source_domain.raw_value, "reason": source_domain.validation_reason},
                )
                diagnostics.append(diagnostic)
                continue
            if source_domain.normalized_domain is None:
                continue

            domain_candidates, scope, domain_diagnostics = discover_domain_candidates(
                source_domain.normalized_domain,
                target_keywords,
                settings=settings,
                client=active_client,
            )
            candidates.extend(domain_candidates)
            scopes.append(scope)
            diagnostics.extend(domain_diagnostics)
    finally:
        if owns_client:
            active_client.close()

    return DiscoveryResult(
        candidates=deduplicate_candidates(candidates),
        scopes=scopes,
        diagnostics=diagnostics,
    )


def discover_domain_candidates(
    source_domain: str,
    target_keywords: Sequence[TargetKeyword],
    *,
    settings: RuntimeSettings = DEFAULT_SETTINGS,
    client: httpx.Client,
) -> tuple[list[CandidatePage], DiscoveryScope, list[str]]:
    """Discover candidate pages for a single normalized source domain."""
    diagnostics: list[str] = []
    homepage = fetch_homepage(source_domain, client=client, diagnostics=diagnostics)
    if homepage is None:
        scope = DiscoveryScope(
            source_domain=source_domain,
            min_recall_sample_count=settings.min_recall_samples,
            depth_2_candidate_count=0,
            expanded_to_depth_3=False,
            final_candidate_count=0,
        )
        return [], scope, diagnostics

    if homepage.redirected:
        diagnostics.append(
            log_runtime_diagnostic(
                LOGGER,
                logging.INFO,
                "首页发生重定向，已使用最终地址继续发现",
                {"domain": source_domain, "url": homepage.url},
            )
        )

    depth_2_candidates = collect_depth_2_candidates(
        source_domain,
        homepage,
        target_keywords,
        settings=settings,
        client=client,
    )
    depth_2_candidates = prioritize_candidates(depth_2_candidates, target_keywords)
    expanded = should_expand_depth(len(depth_2_candidates), settings.min_recall_samples)
    final_candidates = list(depth_2_candidates)

    if expanded:
        diagnostics.append(
            log_runtime_diagnostic(
                LOGGER,
                logging.INFO,
                "深度2候选数量不足，扩展到深度3",
                {
                    "domain": source_domain,
                    "depth_2_count": len(depth_2_candidates),
                    "min_recall_samples": settings.min_recall_samples,
                },
            )
        )
        final_candidates.extend(
            collect_depth_3_candidates(
                source_domain,
                homepage,
                target_keywords,
                settings=settings,
                client=client,
            )
        )

    final_candidates = prioritize_candidates(
        deduplicate_candidates(final_candidates),
        target_keywords,
    )
    scope = DiscoveryScope(
        source_domain=source_domain,
        min_recall_sample_count=settings.min_recall_samples,
        depth_2_candidate_count=len(depth_2_candidates),
        expanded_to_depth_3=expanded,
        expanded_depth=settings.expanded_crawl_depth if expanded else None,
        final_candidate_count=len(final_candidates),
    )
    return final_candidates[: settings.max_pages_per_domain], scope, diagnostics


def fetch_homepage(
    source_domain: str,
    *,
    client: httpx.Client,
    diagnostics: list[str],
) -> FetchedPage | None:
    """Fetch the first accessible HTTP(S) homepage for a source domain."""
    for url in (f"https://{source_domain}/", f"http://{source_domain}/"):
        try:
            response = client.get(url)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            diagnostics.append(
                log_runtime_diagnostic(
                    LOGGER,
                    logging.WARNING,
                    "无法访问源域名首页",
                    {"domain": source_domain, "url": url, "reason": exc.__class__.__name__},
                )
            )
            continue

        content_type = response.headers.get("content-type", "")
        if "html" not in content_type.lower() and not response.text.lstrip().startswith("<"):
            diagnostics.append(
                log_runtime_diagnostic(
                    LOGGER,
                    logging.WARNING,
                    "首页不是可解析的HTML内容，已跳过",
                    {"domain": source_domain, "url": str(response.url)},
                )
            )
            return None

        final_url = str(response.url)
        try:
            final_url = normalize_target_url(final_url, allowed_domain=source_domain)
        except UnsafeUrlError:
            diagnostics.append(
                log_runtime_diagnostic(
                    LOGGER,
                    logging.WARNING,
                    "首页重定向到非同站地址，已跳过",
                    {"domain": source_domain, "url": str(response.url)},
                )
            )
            return None
        return FetchedPage(url=final_url, html=response.text, redirected=final_url != url)

    return None


def collect_depth_2_candidates(
    source_domain: str,
    homepage: FetchedPage,
    target_keywords: Sequence[TargetKeyword],
    *,
    settings: RuntimeSettings,
    client: httpx.Client,
) -> list[CandidatePage]:
    """Collect candidates available from homepage, metadata, and sitemap sources."""
    candidates: list[CandidatePage] = []
    candidates.extend(extract_candidate_links(homepage.html, homepage.url, source_domain))
    candidates.extend(extract_metadata_candidates(homepage.html, homepage.url, source_domain))
    if len(candidates) < settings.min_recall_samples:
        candidates.extend(fetch_sitemap_candidates(source_domain, target_keywords, client=client))
    return deduplicate_candidates(candidates)


def collect_depth_3_candidates(
    source_domain: str,
    homepage: FetchedPage,
    target_keywords: Sequence[TargetKeyword],
    *,
    settings: RuntimeSettings,
    client: httpx.Client,
) -> list[CandidatePage]:
    """Fetch one additional layer of internal pages when depth-2 recall is low."""
    expanded_candidates: list[CandidatePage] = []
    frontier = extract_candidate_links(homepage.html, homepage.url, source_domain)

    for candidate in frontier[: settings.max_pages_per_domain]:
        if candidate.utility_page_flag:
            continue
        try:
            response = client.get(candidate.target_url)
            response.raise_for_status()
        except httpx.HTTPError:
            continue
        page = FetchedPage(url=str(response.url), html=response.text, redirected=False)
        expanded_candidates.extend(extract_candidate_links(page.html, page.url, source_domain))
        expanded_candidates.extend(extract_metadata_candidates(page.html, page.url, source_domain))

    return prioritize_candidates(deduplicate_candidates(expanded_candidates), target_keywords)


def extract_candidate_links(html: str, base_url: str, source_domain: str) -> list[CandidatePage]:
    """Extract normalized same-site link candidates from an HTML document."""
    soup = BeautifulSoup(html, "html.parser")
    candidates: list[CandidatePage] = []
    for anchor in soup.find_all("a", href=True):
        if not isinstance(anchor, Tag):
            continue
        href = str(anchor.get("href", ""))
        candidate_url = normalize_discovered_url(href, base_url, source_domain)
        if candidate_url is None or is_homepage_url(candidate_url):
            continue
        candidates.append(
            build_candidate_page(
                source_domain=source_domain,
                target_url=candidate_url,
                discovery_source=DiscoverySource.INTERNAL_LINK,
            )
        )
    return deduplicate_candidates(candidates)


def extract_metadata_candidates(
    html: str,
    base_url: str,
    source_domain: str,
) -> list[CandidatePage]:
    """Extract candidate URLs from canonical, alternate, OpenGraph, and Twitter metadata."""
    soup = BeautifulSoup(html, "html.parser")
    candidates: list[CandidatePage] = []
    selectors = [
        ("link", "rel", "canonical", "href"),
        ("link", "rel", "alternate", "href"),
        ("meta", "property", "og:url", "content"),
        ("meta", "name", "twitter:url", "content"),
    ]
    for tag_name, match_attr, match_value, value_attr in selectors:
        for tag in soup.find_all(tag_name):
            if not isinstance(tag, Tag):
                continue
            if not tag_attribute_matches(tag, match_attr, match_value):
                continue
            raw_url = str(tag.get(value_attr, ""))
            candidate_url = normalize_discovered_url(raw_url, base_url, source_domain)
            if candidate_url is None or is_homepage_url(candidate_url):
                continue
            candidates.append(
                build_candidate_page(
                    source_domain=source_domain,
                    target_url=candidate_url,
                    discovery_source=DiscoverySource.METADATA,
                    html=html,
                )
            )
    return deduplicate_candidates(candidates)


def fetch_sitemap_candidates(
    source_domain: str,
    target_keywords: Sequence[TargetKeyword],
    *,
    client: httpx.Client,
) -> list[CandidatePage]:
    """Fetch and parse a standard sitemap.xml fallback."""
    sitemap_url = f"https://{source_domain}/sitemap.xml"
    try:
        response = client.get(sitemap_url)
        response.raise_for_status()
    except httpx.HTTPError:
        return []

    candidates: list[CandidatePage] = []
    for raw_url in parse_sitemap_urls(response.text):
        candidate_url = normalize_discovered_url(raw_url, sitemap_url, source_domain)
        if candidate_url is None or is_homepage_url(candidate_url):
            continue
        candidates.append(
            build_candidate_page(
                source_domain=source_domain,
                target_url=candidate_url,
                discovery_source=DiscoverySource.SITEMAP,
            )
        )
    return prioritize_candidates(deduplicate_candidates(candidates), target_keywords)


def parse_sitemap_urls(xml_text: str) -> list[str]:
    """Parse URL locations from a sitemap document."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    urls: list[str] = []
    for element in root.iter():
        if element.tag.endswith("loc") and element.text:
            urls.append(element.text.strip())
    return urls


def build_candidate_page(
    *,
    source_domain: str,
    target_url: str,
    discovery_source: DiscoverySource,
    html: str = "",
) -> CandidatePage:
    """Build a CandidatePage with primary page signals."""
    title = ""
    primary_heading = ""
    core_metadata = ""
    if html:
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.get_text(" ", strip=True) if soup.title else ""
        heading = soup.find("h1")
        primary_heading = heading.get_text(" ", strip=True) if heading else ""
        metadata_values: list[str] = []
        for tag in soup.find_all("meta"):
            if not isinstance(tag, Tag):
                continue
            name = str(tag.get("name", "")).lower()
            property_name = str(tag.get("property", "")).lower()
            if name in {"description", "keywords"} or property_name in {
                "og:title",
                "og:description",
            }:
                metadata_values.append(str(tag.get("content", "")))
        core_metadata = " ".join(value.strip() for value in metadata_values if value.strip())

    return CandidatePage(
        source_domain=source_domain,
        target_url=target_url,
        discovery_source=discovery_source,
        url_slug=url_slug_terms(target_url),
        title=title,
        primary_heading=primary_heading,
        core_metadata=core_metadata,
        utility_page_flag=is_utility_page(target_url),
    )


def prioritize_candidates(
    candidates: Sequence[CandidatePage],
    target_keywords: Sequence[TargetKeyword],
) -> list[CandidatePage]:
    """Sort content-like candidates ahead of weaker or generic candidates."""
    keyword_terms = [keyword.normalized_keyword for keyword in target_keywords]
    return sorted(
        candidates,
        key=lambda candidate: (
            candidate.utility_page_flag,
            -candidate_priority_score(candidate, keyword_terms),
            candidate.target_url,
        ),
    )


def candidate_priority_score(candidate: CandidatePage, keyword_terms: Sequence[str]) -> int:
    """Score a candidate using URL, title, heading, metadata, and keyword evidence."""
    signals = " ".join(
        [
            candidate.url_slug,
            candidate.title,
            candidate.primary_heading,
            candidate.core_metadata,
        ]
    ).lower()
    score = 0
    if any(hint in candidate.url_slug for hint in CONTENT_HINTS):
        score += 30
    if candidate.title:
        score += 15
    if candidate.primary_heading:
        score += 15
    if candidate.core_metadata:
        score += 10
    if any(keyword and keyword in signals for keyword in keyword_terms):
        score += 50
    if candidate.utility_page_flag:
        score -= 100
    return score


def should_expand_depth(depth_2_candidate_count: int, min_recall_sample_count: int) -> bool:
    """Return whether discovery should expand from depth 2 to depth 3."""
    return depth_2_candidate_count < min_recall_sample_count


def normalize_discovered_url(raw_url: str, base_url: str, source_domain: str) -> str | None:
    """Resolve, normalize, and constrain a discovered URL."""
    if not raw_url or raw_url.startswith(("#", "mailto:", "tel:", "javascript:")):
        return None
    absolute_url = urljoin(base_url, raw_url)
    try:
        return normalize_target_url(absolute_url, allowed_domain=source_domain)
    except UnsafeUrlError:
        return None


def deduplicate_candidates(candidates: Iterable[CandidatePage]) -> list[CandidatePage]:
    """Deduplicate candidates by normalized target URL while preserving first occurrence."""
    seen: set[str] = set()
    unique_candidates: list[CandidatePage] = []
    for candidate in candidates:
        try:
            key = normalized_url_key(candidate.target_url, allowed_domain=candidate.source_domain)
        except UnsafeUrlError:
            continue
        if key in seen:
            continue
        seen.add(key)
        unique_candidates.append(candidate)
    return unique_candidates


def is_homepage_url(url: str) -> bool:
    """Return whether a URL points at a domain root homepage."""
    parsed = urlsplit(url)
    path = parsed.path.rstrip("/")
    return path == ""


def url_slug_terms(url: str) -> str:
    """Extract searchable URL slug terms from a URL path."""
    parsed = urlsplit(url)
    path = parsed.path.strip("/")
    return re.sub(r"[-_/]+", " ", path).strip().lower()


def is_utility_page(url: str) -> bool:
    """Return whether a URL path looks like a utility or administrative page."""
    parsed = urlsplit(url)
    path_parts = [part.lower() for part in parsed.path.strip("/").split("/") if part]
    if not path_parts:
        return False
    return any(part in UTILITY_PATH_PARTS for part in path_parts)


def tag_attribute_matches(tag: Tag, attr_name: str, expected_value: str) -> bool:
    """Return whether a BeautifulSoup tag attribute matches a scalar or list value."""
    value = tag.get(attr_name, "")
    if isinstance(value, list):
        return expected_value in [str(item).lower() for item in value]
    return str(value).lower() == expected_value

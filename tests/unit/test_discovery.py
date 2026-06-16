"""Unit tests for candidate discovery helpers."""

import httpx
import respx
from httpx import Response

from wldm_url_filter.config import RuntimeSettings
from wldm_url_filter.discovery import (
    FetchedPage,
    build_candidate_page,
    collect_depth_2_candidates,
    collect_depth_3_candidates,
    discover_candidate_pages,
    extract_candidate_links,
    extract_metadata_candidates,
    fetch_homepage,
    is_utility_page,
    normalize_discovered_url,
    parse_sitemap_urls,
    prioritize_candidates,
    should_expand_depth,
)
from wldm_url_filter.models import DiscoverySource, SourceDomain, TargetKeyword, ValidationStatus


def test_extract_candidate_links_normalizes_same_site_urls_and_rejects_external_links() -> None:
    html = """
    <html><body>
      <a href="/guides/Solar-Panels/?b=2&a=1#details">Guide</a>
      <a href="https://outside.example.net/page">External</a>
      <a href="mailto:test@example.com">Email</a>
      <a href="/">Home</a>
    </body></html>
    """

    candidates = extract_candidate_links(html, "https://example.com/", "example.com")

    assert [candidate.target_url for candidate in candidates] == [
        "https://example.com/guides/Solar-Panels/?a=1&b=2"
    ]
    assert candidates[0].url_slug == "guides solar panels"


def test_should_expand_depth_only_when_depth_two_recall_is_below_threshold() -> None:
    assert should_expand_depth(1, 2) is True
    assert should_expand_depth(2, 2) is False


def test_prioritize_candidates_prefers_keyword_and_content_signals() -> None:
    keywords = [TargetKeyword(keyword="Solar Panels", normalized_keyword="solar panels")]
    generic = build_candidate_page(
        source_domain="example.com",
        target_url="https://example.com/company/about",
        discovery_source=DiscoverySource.INTERNAL_LINK,
    )
    relevant = build_candidate_page(
        source_domain="example.com",
        target_url="https://example.com/guides/solar-panels",
        discovery_source=DiscoverySource.INTERNAL_LINK,
    )

    ordered = prioritize_candidates([generic, relevant], keywords)

    assert ordered[0].target_url == "https://example.com/guides/solar-panels"
    assert ordered[-1].utility_page_flag is True


def test_collect_depth_2_candidates_uses_metadata_before_sitemap_fallback() -> None:
    html = """
    <html><head>
      <meta property="og:url" content="/reviews/solar-panels">
      <title>Solar Panels</title>
    </head><body></body></html>
    """
    client = httpx.Client(base_url="https://example.com")

    candidates = collect_depth_2_candidates(
        "example.com",
        homepage=FetchedPage(url="https://example.com/", html=html, redirected=False),
        target_keywords=[TargetKeyword(keyword="Solar Panels", normalized_keyword="solar panels")],
        settings=RuntimeSettings(min_recall_samples=1),
        client=client,
    )

    assert [candidate.discovery_source for candidate in candidates] == [DiscoverySource.METADATA]
    assert candidates[0].target_url == "https://example.com/reviews/solar-panels"


def test_utility_page_detection_covers_common_paths() -> None:
    assert is_utility_page("https://example.com/about") is True
    assert is_utility_page("https://example.com/blog/solar-panels") is False


def test_build_candidate_page_extracts_primary_html_signals() -> None:
    html = """
    <html><head>
      <title>Solar Reviews</title>
      <meta name="description" content="Detailed solar panel reviews">
      <meta property="og:description" content="Best panels">
    </head><body><h1>Solar Panel Guide</h1></body></html>
    """

    candidate = build_candidate_page(
        source_domain="example.com",
        target_url="https://example.com/reviews/solar-panels",
        discovery_source=DiscoverySource.METADATA,
        html=html,
    )

    assert candidate.title == "Solar Reviews"
    assert candidate.primary_heading == "Solar Panel Guide"
    assert "Detailed solar panel reviews" in candidate.core_metadata


def test_extract_metadata_candidates_reads_canonical_alternate_and_twitter_urls() -> None:
    html = """
    <html><head>
      <link rel="canonical" href="/canonical/solar">
      <link rel="alternate" href="/alternate/solar">
      <meta name="twitter:url" content="/twitter/solar">
    </head></html>
    """

    candidates = extract_metadata_candidates(html, "https://example.com/", "example.com")

    assert [candidate.target_url for candidate in candidates] == [
        "https://example.com/canonical/solar",
        "https://example.com/alternate/solar",
        "https://example.com/twitter/solar",
    ]


def test_parse_sitemap_urls_returns_empty_list_for_invalid_xml() -> None:
    assert parse_sitemap_urls("<not-valid") == []


def test_normalize_discovered_url_rejects_unsafe_and_non_http_values() -> None:
    assert (
        normalize_discovered_url("mailto:test@example.com", "https://example.com/", "example.com")
        is None
    )
    assert (
        normalize_discovered_url(
            "https://evil.example.net/a",
            "https://example.com/",
            "example.com",
        )
        is None
    )


def test_fetch_homepage_reports_inaccessible_domain(respx_mock: respx.MockRouter) -> None:
    respx_mock.get("https://offline.example/").mock(return_value=Response(503))
    respx_mock.get("http://offline.example/").mock(return_value=Response(503))
    diagnostics: list[str] = []

    with httpx.Client(follow_redirects=True) as client:
        page = fetch_homepage("offline.example", client=client, diagnostics=diagnostics)

    assert page is None
    assert diagnostics
    assert all("无法访问源域名首页" in diagnostic for diagnostic in diagnostics)


def test_fetch_homepage_rejects_non_html_content(respx_mock: respx.MockRouter) -> None:
    respx_mock.get("https://binary.example/").mock(
        return_value=Response(200, content=b"not html", headers={"content-type": "application/pdf"})
    )
    diagnostics: list[str] = []

    with httpx.Client(follow_redirects=True) as client:
        page = fetch_homepage("binary.example", client=client, diagnostics=diagnostics)

    assert page is None
    assert any("不是可解析的HTML" in diagnostic for diagnostic in diagnostics)


def test_discover_candidate_pages_skips_invalid_domains() -> None:
    invalid = SourceDomain(
        raw_value="localhost",
        input_row_number=2,
        validation_status=ValidationStatus.INVALID,
        validation_reason="Unsafe host",
    )

    result = discover_candidate_pages([invalid], [])

    assert result.candidates == []
    assert "跳过无效或重复的源域名" in result.diagnostics[0]


def test_collect_depth_3_candidates_skips_utility_frontier_pages(
    respx_mock: respx.MockRouter,
) -> None:
    homepage = FetchedPage(
        url="https://example.com/",
        html='<a href="/about">About</a><a href="/topics">Topics</a>',
        redirected=False,
    )
    respx_mock.get("https://example.com/topics").mock(
        return_value=Response(
            200,
            html='<a href="/topics/solar-panels">Solar Panels</a>',
            headers={"content-type": "text/html"},
        )
    )

    with httpx.Client(follow_redirects=True) as client:
        candidates = collect_depth_3_candidates(
            "example.com",
            homepage,
            [TargetKeyword(keyword="Solar Panels", normalized_keyword="solar panels")],
            settings=RuntimeSettings(min_recall_samples=2),
            client=client,
        )

    assert [candidate.target_url for candidate in candidates] == [
        "https://example.com/topics/solar-panels"
    ]

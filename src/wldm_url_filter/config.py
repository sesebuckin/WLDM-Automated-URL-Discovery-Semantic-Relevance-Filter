"""Runtime configuration and URL safety helpers for the URL discovery pipeline."""

from __future__ import annotations

import re
from dataclasses import dataclass
from ipaddress import ip_address
from posixpath import normpath
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit


@dataclass(frozen=True, slots=True)
class RuntimeSettings:
    """Shared runtime settings used by pipeline services."""

    fast_pass_timeout_seconds: float = 5.0
    timeout_retest_seconds: float = 20.0
    fast_pass_concurrency: int = 50
    timeout_retest_concurrency: int = 1
    max_pages_per_domain: int = 50
    initial_crawl_depth: int = 2
    expanded_crawl_depth: int = 3
    min_recall_samples: int = 1
    target_failure_rate: float = 0.10


DEFAULT_SETTINGS = RuntimeSettings()


class UnsafeUrlError(ValueError):
    """Raised when an input host or URL is unsafe for network access."""


_HOST_LABEL_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
_LOCAL_SUFFIXES = (".local", ".localhost", ".internal")
_UNSAFE_HOSTNAMES = {"localhost", "0.0.0.0"}


def normalize_domain_value(raw_value: str) -> str:
    """Normalize a source-domain input cell into a safe canonical host."""
    value = raw_value.strip()
    if not value:
        raise UnsafeUrlError("Blank domain")

    parsed = urlsplit(value if "://" in value else f"http://{value}")
    if parsed.username or parsed.password:
        raise UnsafeUrlError("Credentials are not allowed in domain values")

    host = parsed.hostname
    if not host:
        raise UnsafeUrlError("Missing host")

    normalized = _normalize_host(host)
    if normalized.startswith("www."):
        normalized = normalized[4:]
    return normalized


def normalize_target_url(raw_url: str, *, allowed_domain: str | None = None) -> str:
    """Normalize an absolute HTTP(S) URL and reject unsafe hosts."""
    value = raw_url.strip()
    if not value:
        raise UnsafeUrlError("Blank URL")

    parsed = urlsplit(value)
    if parsed.scheme.lower() not in {"http", "https"}:
        raise UnsafeUrlError("Only http and https URLs are allowed")
    if parsed.username or parsed.password:
        raise UnsafeUrlError("Credentials are not allowed in URLs")
    if not parsed.hostname:
        raise UnsafeUrlError("Missing host")

    host = _normalize_host(parsed.hostname)
    if allowed_domain is not None:
        normalized_allowed_domain = normalize_domain_value(allowed_domain)
        if not is_same_site(host, normalized_allowed_domain):
            raise UnsafeUrlError("URL host is outside the allowed source domain")

    port = parsed.port
    netloc = host
    if port is not None and not (
        (parsed.scheme.lower() == "http" and port == 80)
        or (parsed.scheme.lower() == "https" and port == 443)
    ):
        netloc = f"{host}:{port}"

    path = _normalize_path(parsed.path)
    query = _normalize_query(parsed.query)
    return urlunsplit((parsed.scheme.lower(), netloc, path, query, ""))


def normalized_url_key(raw_url: str, *, allowed_domain: str | None = None) -> str:
    """Return the duplicate-detection key for a target URL."""
    normalized = normalize_target_url(raw_url, allowed_domain=allowed_domain)
    parsed = urlsplit(normalized)
    path = parsed.path.rstrip("/") or "/"
    return urlunsplit((parsed.scheme, parsed.netloc, path, parsed.query, ""))


def find_duplicate_normalized_urls(raw_urls: list[str]) -> set[str]:
    """Return normalized URL keys that appear more than once in an input list."""
    seen: set[str] = set()
    duplicates: set[str] = set()
    for raw_url in raw_urls:
        key = normalized_url_key(raw_url)
        if key in seen:
            duplicates.add(key)
        seen.add(key)
    return duplicates


def is_same_site(host: str, allowed_domain: str) -> bool:
    """Return whether host is the allowed domain or one of its subdomains."""
    normalized_host = _normalize_host(host)
    normalized_domain = _normalize_host(allowed_domain)
    return normalized_host == normalized_domain or normalized_host.endswith(f".{normalized_domain}")


def is_unsafe_host(host: str) -> bool:
    """Return whether a host is local, private, malformed, or otherwise unsafe."""
    try:
        normalized = host.strip().lower().rstrip(".")
    except AttributeError:
        return True
    if not normalized or normalized in _UNSAFE_HOSTNAMES or normalized.endswith(_LOCAL_SUFFIXES):
        return True

    try:
        address = ip_address(normalized)
    except ValueError:
        return not _is_valid_hostname(normalized)

    return (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    )


def _normalize_host(host: str) -> str:
    normalized = host.strip().lower().rstrip(".")
    if is_unsafe_host(normalized):
        raise UnsafeUrlError(f"Unsafe host: {host}")
    return normalized


def _is_valid_hostname(host: str) -> bool:
    if len(host) > 253 or "." not in host:
        return False
    labels = host.split(".")
    return all(_HOST_LABEL_PATTERN.fullmatch(label) for label in labels)


def _normalize_path(path: str) -> str:
    if not path:
        return "/"
    normalized = normpath(path)
    if path.endswith("/") and not normalized.endswith("/"):
        normalized = f"{normalized}/"
    if not normalized.startswith("/"):
        normalized = f"/{normalized}"
    return quote(normalized, safe="/%:@")


def _normalize_query(query: str) -> str:
    if not query:
        return ""
    pairs = parse_qsl(query, keep_blank_values=True)
    pairs.sort()
    return urlencode(pairs, doseq=True)

"""Unit tests for URL normalization and unsafe-host rejection."""

import pytest

from wldm_url_filter.config import (
    UnsafeUrlError,
    find_duplicate_normalized_urls,
    is_same_site,
    normalize_domain_value,
    normalize_target_url,
)


def test_normalize_domain_removes_protocol_path_and_www_prefix() -> None:
    assert normalize_domain_value("HTTPS://www.Example.com/path?q=1") == "example.com"


@pytest.mark.parametrize(
    "raw_value",
    [
        "localhost",
        "http://127.0.0.1",
        "http://10.0.0.4",
        "http://example.local",
        "not-a-host",
    ],
)
def test_normalize_domain_rejects_unsafe_hosts(raw_value: str) -> None:
    with pytest.raises(UnsafeUrlError):
        normalize_domain_value(raw_value)


def test_normalize_target_url_sorts_query_and_removes_fragment() -> None:
    normalized = normalize_target_url("HTTPS://Example.com/a/../b?z=2&a=1#secret")

    assert normalized == "https://example.com/b?a=1&z=2"


def test_normalize_target_url_blocks_external_allowed_domain() -> None:
    with pytest.raises(UnsafeUrlError):
        normalize_target_url("https://other.example.net/page", allowed_domain="example.com")


def test_find_duplicate_normalized_urls_collapses_equivalent_urls() -> None:
    duplicates = find_duplicate_normalized_urls(
        [
            "https://example.com/page/?b=2&a=1",
            "https://example.com/page?a=1&b=2#frag",
            "https://example.com/other",
        ]
    )

    assert duplicates == {"https://example.com/page?a=1&b=2"}


def test_same_site_allows_subdomains_only() -> None:
    assert is_same_site("blog.example.com", "example.com") is True
    assert is_same_site("badexample.com", "example.com") is False

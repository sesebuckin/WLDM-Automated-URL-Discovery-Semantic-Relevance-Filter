"""Integration tests for candidate discovery flow with mocked HTTP."""

import httpx
import pytest
import respx
from httpx import Response

from wldm_url_filter.config import RuntimeSettings
from wldm_url_filter.discovery import discover_candidate_pages
from wldm_url_filter.models import SourceDomain, TargetKeyword, ValidationStatus


def valid_domain(domain: str) -> SourceDomain:
    """Create a valid SourceDomain fixture."""
    return SourceDomain(
        raw_value=domain,
        normalized_domain=domain,
        input_row_number=2,
        validation_status=ValidationStatus.VALID,
    )


def keyword(value: str) -> TargetKeyword:
    """Create a TargetKeyword fixture."""
    return TargetKeyword(keyword=value, normalized_keyword=value.lower())


@pytest.mark.parametrize("domain", ["relevant.example", "junk.example"])
def test_discovery_emits_deep_relevant_urls_without_homepage_only_matches(
    respx_mock: respx.MockRouter,
    domain: str,
) -> None:
    if domain == "relevant.example":
        homepage = '<a href="/guides/solar-panels">Solar guide</a><a href="/about">About</a>'
        page = "<html><title>Solar Panels Guide</title><h1>Solar Panels</h1></html>"
        respx_mock.get(f"https://{domain}/").mock(
            return_value=Response(200, html=homepage, headers={"content-type": "text/html"})
        )
        respx_mock.get(f"https://{domain}/guides/solar-panels").mock(
            return_value=Response(200, html=page, headers={"content-type": "text/html"})
        )
    else:
        homepage = '<a href="/">Home</a><a href="/about">About</a>'
        respx_mock.get(f"https://{domain}/").mock(
            return_value=Response(200, html=homepage, headers={"content-type": "text/html"})
        )

    with httpx.Client(follow_redirects=True) as client:
        result = discover_candidate_pages(
            [valid_domain(domain)],
            [keyword("solar panels")],
            settings=RuntimeSettings(min_recall_samples=1),
            client=client,
        )

    candidate_urls = [candidate.target_url for candidate in result.candidates]
    assert f"https://{domain}/" not in candidate_urls
    if domain == "relevant.example":
        assert f"https://{domain}/guides/solar-panels" in candidate_urls
    else:
        assert candidate_urls == [f"https://{domain}/about"]
        assert result.candidates[0].utility_page_flag is True


def test_discovery_handles_redirecting_homepage(respx_mock: respx.MockRouter) -> None:
    respx_mock.get("https://redirect.example/").mock(
        return_value=Response(
            302,
            headers={"location": "https://redirect.example/home"},
        )
    )
    respx_mock.get("https://redirect.example/home").mock(
        return_value=Response(
            200,
            html='<a href="/reviews/solar-panels">Review</a>',
            headers={"content-type": "text/html"},
        )
    )

    with httpx.Client(follow_redirects=True) as client:
        result = discover_candidate_pages(
            [valid_domain("redirect.example")],
            [keyword("solar panels")],
            settings=RuntimeSettings(min_recall_samples=1),
            client=client,
        )

    assert result.candidates[0].target_url == "https://redirect.example/reviews/solar-panels"
    assert any("重定向" in diagnostic for diagnostic in result.diagnostics)


def test_discovery_uses_sitemap_when_homepage_has_no_candidates(
    respx_mock: respx.MockRouter,
) -> None:
    respx_mock.get("https://sitemap.example/").mock(
        return_value=Response(200, html="<html></html>", headers={"content-type": "text/html"})
    )
    respx_mock.get("https://sitemap.example/sitemap.xml").mock(
        return_value=Response(
            200,
            text=(
                "<urlset>"
                "<url><loc>https://sitemap.example/blog/solar-panels</loc></url>"
                "</urlset>"
            ),
        )
    )

    with httpx.Client(follow_redirects=True) as client:
        result = discover_candidate_pages(
            [valid_domain("sitemap.example")],
            [keyword("solar panels")],
            settings=RuntimeSettings(min_recall_samples=1),
            client=client,
        )

    assert result.candidates[0].target_url == "https://sitemap.example/blog/solar-panels"


def test_discovery_expands_to_depth_three_when_depth_two_recall_is_low(
    respx_mock: respx.MockRouter,
) -> None:
    respx_mock.get("https://depth.example/").mock(
        return_value=Response(
            200,
            html='<a href="/topics">Topics</a>',
            headers={"content-type": "text/html"},
        )
    )
    respx_mock.get("https://depth.example/topics").mock(
        return_value=Response(
            200,
            html='<a href="/topics/solar-panels-guide">Solar panels guide</a>',
            headers={"content-type": "text/html"},
        )
    )
    respx_mock.get("https://depth.example/sitemap.xml").mock(return_value=Response(404))

    with httpx.Client(follow_redirects=True) as client:
        result = discover_candidate_pages(
            [valid_domain("depth.example")],
            [keyword("solar panels")],
            settings=RuntimeSettings(min_recall_samples=2),
            client=client,
        )

    assert result.scopes[0].expanded_to_depth_3 is True
    assert "https://depth.example/topics/solar-panels-guide" in [
        candidate.target_url for candidate in result.candidates
    ]

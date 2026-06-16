"""Integration tests for candidate-to-accepted relevance decisions."""

from wldm_url_filter.models import CandidatePage, DiscoverySource, TargetKeyword
from wldm_url_filter.relevance import filter_relevant_candidates


def candidate(
    target_url: str,
    *,
    url_slug: str,
    title: str = "",
    primary_heading: str = "",
    core_metadata: str = "",
    utility_page_flag: bool = False,
) -> CandidatePage:
    """Create a CandidatePage fixture."""
    return CandidatePage(
        source_domain="example.com",
        target_url=target_url,
        discovery_source=DiscoverySource.INTERNAL_LINK,
        url_slug=url_slug,
        title=title,
        primary_heading=primary_heading,
        core_metadata=core_metadata,
        utility_page_flag=utility_page_flag,
    )


def test_relevance_flow_accepts_matches_and_discards_irrelevant_pages() -> None:
    keywords = [TargetKeyword(keyword="Solar Panels", normalized_keyword="solar panels")]
    candidates = [
        candidate(
            "https://example.com/guides/solar-panels",
            url_slug="guides solar panels",
            title="Solar Panels Guide",
        ),
        candidate(
            "https://example.com/reviews/solar-panel",
            url_slug="reviews solar panel",
            primary_heading="Solar panel review",
        ),
        candidate(
            "https://example.com/about/solar-panels",
            url_slug="about solar panels",
            title="Solar Panels",
            utility_page_flag=True,
        ),
        candidate(
            "https://example.com/company-news",
            url_slug="company news",
            title="Company News",
        ),
    ]

    result = filter_relevant_candidates(candidates, keywords)

    assert [match.target_url for match in result.accepted_matches] == [
        "https://example.com/guides/solar-panels",
        "https://example.com/reviews/solar-panel",
    ]
    assert len(result.decisions) == 4
    assert any("候选页面匹配目标关键词" in diagnostic for diagnostic in result.diagnostics)
    assert any("候选页面未通过相关性过滤" in diagnostic for diagnostic in result.diagnostics)

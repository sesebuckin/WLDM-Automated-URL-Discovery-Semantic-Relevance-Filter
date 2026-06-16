"""Unit tests for utility-page exclusions."""

from wldm_url_filter.models import CandidatePage, DiscoverySource, TargetKeyword
from wldm_url_filter.relevance import evaluate_candidate_relevance


def test_utility_page_flag_overrides_keyword_evidence() -> None:
    candidate = CandidatePage(
        source_domain="example.com",
        target_url="https://example.com/about/solar-panels",
        discovery_source=DiscoverySource.INTERNAL_LINK,
        url_slug="about solar panels",
        title="Solar Panels",
        utility_page_flag=True,
    )

    decision = evaluate_candidate_relevance(
        candidate,
        [TargetKeyword(keyword="Solar Panels", normalized_keyword="solar panels")],
    )

    assert decision.matched is False
    assert decision.exclusion_reason == "utility_page"


def test_utility_url_terms_override_incidental_keyword_evidence() -> None:
    candidate = CandidatePage(
        source_domain="example.com",
        target_url="https://example.com/contact",
        discovery_source=DiscoverySource.INTERNAL_LINK,
        url_slug="contact",
        core_metadata="Solar Panels support desk",
        utility_page_flag=False,
    )

    decision = evaluate_candidate_relevance(
        candidate,
        [TargetKeyword(keyword="Solar Panels", normalized_keyword="solar panels")],
    )

    assert decision.matched is False
    assert decision.exclusion_reason == "utility_page"

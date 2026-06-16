"""Unit tests for keyword and semantic relevance matching."""

from wldm_url_filter.models import (
    CandidatePage,
    DiscoverySource,
    MatchedSignal,
    MatchType,
    TargetKeyword,
)
from wldm_url_filter.relevance import (
    accepted_urls_from_candidates,
    evaluate_candidate_relevance,
    extract_primary_signals,
    normalize_signal,
)


def keyword(value: str) -> TargetKeyword:
    """Create a TargetKeyword fixture."""
    return TargetKeyword(keyword=value, normalized_keyword=normalize_signal(value))


def candidate(**overrides: object) -> CandidatePage:
    """Create a CandidatePage fixture."""
    values = {
        "source_domain": "example.com",
        "target_url": "https://example.com/guides/solar-panels",
        "discovery_source": DiscoverySource.INTERNAL_LINK,
        "url_slug": "guides solar panels",
        "title": "",
        "primary_heading": "",
        "core_metadata": "",
        "utility_page_flag": False,
    }
    values.update(overrides)
    return CandidatePage(**values)


def test_extract_primary_signals_normalizes_text() -> None:
    signals = extract_primary_signals(
        candidate(title="Best Solar-Panels!!!", primary_heading="  Solar   Panels  ")
    )

    assert signals.title == "best solar panels"
    assert signals.primary_heading == "solar panels"


def test_exact_keyword_match_prefers_primary_signal_evidence() -> None:
    decision = evaluate_candidate_relevance(
        candidate(title="A Complete Solar Panels Guide"),
        [keyword("Solar Panels")],
    )

    assert decision.matched is True
    assert decision.detected_keyword == "Solar Panels"
    assert decision.matched_signal == MatchedSignal.URL_SLUG
    assert decision.match_type == MatchType.EXACT_KEYWORD
    assert decision.relevance_score == 100


def test_close_semantic_variant_match_accepts_strong_lexical_variants() -> None:
    decision = evaluate_candidate_relevance(
        candidate(url_slug="guides solar panel", title="Solar panel guide"),
        [keyword("Solar Panels")],
    )

    assert decision.matched is True
    assert decision.match_type == MatchType.CLOSE_SEMANTIC_VARIANT
    assert decision.relevance_score > 70


def test_no_primary_signal_match_is_rejected() -> None:
    decision = evaluate_candidate_relevance(
        candidate(url_slug="company news", title="Company update"),
        [keyword("Solar Panels")],
    )

    assert decision.matched is False
    assert decision.exclusion_reason == "no_primary_signal_match"


def test_accepted_urls_preserve_strongest_duplicate_target_url() -> None:
    weak = candidate(
        target_url="https://example.com/guides/solar-panels/",
        url_slug="guides solar panel",
    )
    strong = candidate(
        target_url="https://example.com/guides/solar-panels",
        url_slug="guides solar panels",
    )

    accepted = accepted_urls_from_candidates([weak, strong], [keyword("Solar Panels")])

    assert len(accepted) == 1
    assert accepted[0].target_url == "https://example.com/guides/solar-panels"
    assert accepted[0].relevance_score == 100

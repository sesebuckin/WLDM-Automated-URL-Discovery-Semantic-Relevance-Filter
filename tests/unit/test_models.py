"""Unit tests for shared pipeline data models."""

import pytest
from pydantic import ValidationError

from wldm_url_filter.models import (
    AcceptedUrlMatch,
    AccessOutcome,
    AccessReliabilitySummary,
    AccessStage,
    CandidatePage,
    DiscoveryScope,
    DiscoverySource,
    FailureType,
    MatchedSignal,
    MatchType,
    OptimizationStatus,
    ProcessingSummary,
    RelevanceDecision,
    SourceDomain,
    TargetKeyword,
    TargetUrlAccessAttempt,
    ValidationStatus,
)


def test_source_domain_requires_normalized_domain_when_valid() -> None:
    with pytest.raises(ValidationError):
        SourceDomain(
            raw_value="example.com",
            input_row_number=2,
            validation_status=ValidationStatus.VALID,
        )


def test_source_domain_allows_invalid_record_with_reason() -> None:
    domain = SourceDomain(
        raw_value="localhost",
        input_row_number=3,
        validation_status=ValidationStatus.INVALID,
        validation_reason="Unsafe host",
    )

    assert domain.normalized_domain is None


def test_candidate_page_and_keyword_models_accept_expected_values() -> None:
    keyword = TargetKeyword(keyword="Solar Panels", normalized_keyword="solar panels")
    page = CandidatePage(
        source_domain="example.com",
        target_url="https://example.com/guides/solar-panels",
        discovery_source=DiscoverySource.INTERNAL_LINK,
        url_slug="guides solar panels",
        title="Solar Panels Guide",
    )

    assert keyword.normalized_keyword == "solar panels"
    assert page.discovery_source == DiscoverySource.INTERNAL_LINK


def test_discovery_scope_blocks_unnecessary_depth_expansion() -> None:
    with pytest.raises(ValidationError):
        DiscoveryScope(
            source_domain="example.com",
            min_recall_sample_count=3,
            depth_2_candidate_count=3,
            expanded_to_depth_3=True,
            expanded_depth=3,
            final_candidate_count=4,
        )


def test_access_attempt_requires_failure_type_for_failures() -> None:
    with pytest.raises(ValidationError):
        TargetUrlAccessAttempt(
            target_url="https://example.com/page",
            stage=AccessStage.FAST_PASS,
            outcome=AccessOutcome.FAILURE,
            elapsed_ms=50,
        )


def test_relevance_decision_requires_evidence_when_matched() -> None:
    decision = RelevanceDecision(
        target_url="https://example.com/page",
        matched=True,
        detected_keyword="solar panels",
        matched_signal=MatchedSignal.TITLE,
        match_type=MatchType.EXACT_KEYWORD,
        relevance_score=95,
    )

    assert decision.matched is True


def test_accepted_url_match_requires_score_range() -> None:
    with pytest.raises(ValidationError):
        AcceptedUrlMatch(
            source_domain="example.com",
            target_url="https://example.com/page",
            detected_keyword="solar",
            relevance_score=101,
        )


def test_access_reliability_rates_must_sum_to_one_hundred() -> None:
    with pytest.raises(ValidationError):
        AccessReliabilitySummary(
            success_count=8,
            success_rate=80,
            failure_count=2,
            failure_rate=15,
            failure_type=FailureType.TIMEOUT,
            failure_type_count=2,
        )


def test_processing_summary_validates_count_consistency() -> None:
    summary = ProcessingSummary(
        total_input_rows=4,
        valid_domains=2,
        invalid_domains=1,
        duplicate_domains=1,
        domains_attempted=2,
        domains_with_matches=1,
        accepted_url_count=2,
        excluded_candidate_count=3,
        inaccessible_domain_count=1,
        optimization_status=OptimizationStatus.READY,
    )

    assert summary.total_input_rows == 4

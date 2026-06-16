"""Unit tests for reachability classification and summaries."""

import httpx
from httpx import Response

from wldm_url_filter.models import (
    AccessOutcome,
    AccessStage,
    CandidatePage,
    DiscoverySource,
    FailureType,
    OptimizationStatus,
    TargetUrlAccessAttempt,
)
from wldm_url_filter.reachability import (
    build_access_reliability_rows,
    classify_response_failure,
    determine_optimization_status,
    failure_rate,
    final_attempts_after_retests,
)


def candidate(url: str) -> CandidatePage:
    """Create a CandidatePage fixture."""
    return CandidatePage(
        source_domain="example.com",
        target_url=url,
        discovery_source=DiscoverySource.INTERNAL_LINK,
    )


def attempt(
    url: str,
    outcome: AccessOutcome,
    failure_type: FailureType = FailureType.NONE,
) -> TargetUrlAccessAttempt:
    """Create a TargetUrlAccessAttempt fixture."""
    return TargetUrlAccessAttempt(
        target_url=url,
        stage=AccessStage.FAST_PASS,
        outcome=outcome,
        failure_type=failure_type,
        elapsed_ms=1,
    )


def test_classify_response_failure_maps_blocked_redirect_and_content_types() -> None:
    redirect = Response(302, headers={"location": "https://other.example.net/"})
    redirect.request = httpx.Request("GET", "https://example.com/page")
    blocked = Response(403, request=httpx.Request("GET", "https://example.com/page"))
    pdf = Response(
        200,
        headers={"content-type": "application/pdf"},
        request=httpx.Request("GET", "https://example.com/page"),
    )
    html = Response(
        200,
        headers={"content-type": "text/html"},
        request=httpx.Request("GET", "https://example.com/page"),
    )

    assert (
        classify_response_failure(redirect, "https://example.com/page")
        == FailureType.REDIRECT_FAILURE
    )
    assert (
        classify_response_failure(blocked, "https://example.com/page")
        == FailureType.BLOCKED_ACCESS
    )
    assert (
        classify_response_failure(pdf, "https://example.com/page")
        == FailureType.UNSUPPORTED_CONTENT
    )
    assert classify_response_failure(html, "https://example.com/page") == FailureType.NONE


def test_final_attempts_replace_timeout_fast_pass_with_retest_result() -> None:
    timeout = attempt("https://example.com/a", AccessOutcome.FAILURE, FailureType.TIMEOUT)
    blocked = attempt("https://example.com/b", AccessOutcome.FAILURE, FailureType.BLOCKED_ACCESS)
    retest = TargetUrlAccessAttempt(
        target_url="https://example.com/a",
        stage=AccessStage.TIMEOUT_RETEST,
        outcome=AccessOutcome.SUCCESS,
        failure_type=FailureType.NONE,
        elapsed_ms=1,
        was_retested=True,
    )

    final_attempts = final_attempts_after_retests([timeout, blocked], [retest])

    assert final_attempts == [retest, blocked]


def test_access_reliability_rows_group_failures_by_type() -> None:
    rows = build_access_reliability_rows(
        [
            attempt("https://example.com/a", AccessOutcome.SUCCESS),
            attempt("https://example.com/b", AccessOutcome.FAILURE, FailureType.BLOCKED_ACCESS),
            attempt("https://example.com/c", AccessOutcome.FAILURE, FailureType.BLOCKED_ACCESS),
        ]
    )

    assert len(rows) == 1
    assert rows[0].success_count == 1
    assert rows[0].failure_count == 2
    assert rows[0].failure_type == FailureType.BLOCKED_ACCESS
    assert rows[0].failure_type_count == 2


def test_optimization_status_respects_threshold_and_requester_acceptance() -> None:
    attempts = [
        attempt("https://example.com/a", AccessOutcome.SUCCESS),
        attempt("https://example.com/b", AccessOutcome.FAILURE, FailureType.TIMEOUT),
    ]

    assert failure_rate(attempts) == 0.5
    assert (
        determine_optimization_status(
            attempts,
            target_failure_rate=0.1,
            requester_accepted_failures=False,
        )
        == OptimizationStatus.OPTIMIZE_AGAIN
    )
    assert (
        determine_optimization_status(
            attempts,
            target_failure_rate=0.1,
            requester_accepted_failures=True,
        )
        == OptimizationStatus.ACCEPTED_BY_REQUESTER
    )

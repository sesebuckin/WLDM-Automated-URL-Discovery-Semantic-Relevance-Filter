"""Integration tests for two-stage reachability flow."""

import httpx
import pytest
import respx
from httpx import Response

from wldm_url_filter.config import RuntimeSettings
from wldm_url_filter.models import CandidatePage, DiscoverySource, FailureType, OptimizationStatus
from wldm_url_filter.reachability import evaluate_reachability


def candidate(url: str) -> CandidatePage:
    """Create a CandidatePage fixture."""
    return CandidatePage(
        source_domain="example.com",
        target_url=url,
        discovery_source=DiscoverySource.INTERNAL_LINK,
    )


def test_reachability_fast_pass_success(respx_mock: respx.MockRouter) -> None:
    respx_mock.get("https://example.com/a").mock(
        return_value=Response(200, headers={"content-type": "text/html"})
    )

    with httpx.Client(follow_redirects=False) as client:
        result = evaluate_reachability(
            [candidate("https://example.com/a")],
            settings=RuntimeSettings(target_failure_rate=0.1),
            client=client,
        )

    assert result.final_attempts[0].failure_type == FailureType.NONE
    assert result.optimization_status == OptimizationStatus.READY


def test_reachability_retests_timeout_success(respx_mock: respx.MockRouter) -> None:
    route = respx_mock.get("https://example.com/slow")
    route.side_effect = [
        httpx.TimeoutException("timeout"),
        Response(200, headers={"content-type": "text/html"}),
    ]

    with httpx.Client(follow_redirects=False) as client:
        result = evaluate_reachability(
            [candidate("https://example.com/slow")],
            settings=RuntimeSettings(target_failure_rate=0.1),
            client=client,
        )

    assert len(result.attempts) == 2
    assert result.final_attempts[0].was_retested is True
    assert result.final_attempts[0].failure_type == FailureType.NONE
    assert any("正在重试超时目标网址" in diagnostic for diagnostic in result.diagnostics)


@pytest.mark.parametrize(
    ("url", "response", "failure_type"),
    [
        (
            "https://example.com/blocked",
            Response(403, headers={"content-type": "text/html"}),
            FailureType.BLOCKED_ACCESS,
        ),
        (
            "https://example.com/redirect",
            Response(302, headers={"location": "https://other.example.net/"}),
            FailureType.REDIRECT_FAILURE,
        ),
        (
            "https://example.com/file.pdf",
            Response(200, headers={"content-type": "application/pdf"}),
            FailureType.UNSUPPORTED_CONTENT,
        ),
    ],
)
def test_reachability_classifies_failures(
    respx_mock: respx.MockRouter,
    url: str,
    response: Response,
    failure_type: FailureType,
) -> None:
    respx_mock.get(url).mock(return_value=response)

    with httpx.Client(follow_redirects=False) as client:
        result = evaluate_reachability(
            [candidate(url)],
            settings=RuntimeSettings(target_failure_rate=0.1),
            client=client,
        )

    assert result.final_attempts[0].failure_type == failure_type
    assert result.optimization_status == OptimizationStatus.OPTIMIZE_AGAIN


def test_reachability_requester_acceptance_allows_high_failure_rate(
    respx_mock: respx.MockRouter,
) -> None:
    respx_mock.get("https://example.com/blocked").mock(
        return_value=Response(403, headers={"content-type": "text/html"})
    )

    with httpx.Client(follow_redirects=False) as client:
        result = evaluate_reachability(
            [candidate("https://example.com/blocked")],
            settings=RuntimeSettings(target_failure_rate=0.1),
            requester_accepted_failures=True,
            client=client,
        )

    assert result.optimization_status == OptimizationStatus.ACCEPTED_BY_REQUESTER

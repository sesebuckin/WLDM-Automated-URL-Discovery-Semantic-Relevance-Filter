"""Target URL reachability checks and access reliability summaries."""

from __future__ import annotations

import logging
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from time import monotonic
from urllib.parse import urlsplit

import httpx

from wldm_url_filter.config import (
    DEFAULT_SETTINGS,
    RuntimeSettings,
    UnsafeUrlError,
    normalize_target_url,
)
from wldm_url_filter.logging_config import log_runtime_diagnostic
from wldm_url_filter.models import (
    AccessOutcome,
    AccessReliabilitySummary,
    AccessStage,
    CandidatePage,
    FailureType,
    OptimizationStatus,
    TargetUrlAccessAttempt,
)

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ReachabilityResult:
    """Reachability attempts, final attempts, reliability rows, and run status."""

    attempts: list[TargetUrlAccessAttempt]
    final_attempts: list[TargetUrlAccessAttempt]
    reliability_rows: list[AccessReliabilitySummary]
    optimization_status: OptimizationStatus
    diagnostics: list[str]


def evaluate_reachability(
    candidates: Sequence[CandidatePage],
    *,
    settings: RuntimeSettings = DEFAULT_SETTINGS,
    requester_accepted_failures: bool = False,
    client: httpx.Client | None = None,
) -> ReachabilityResult:
    """Run fast reachability checks and timeout-only retests for candidate URLs."""
    owns_client = client is None
    active_client = client or httpx.Client(
        follow_redirects=False,
        timeout=settings.fast_pass_timeout_seconds,
    )
    diagnostics: list[str] = []

    try:
        fast_attempts = run_fast_reachability_pass(
            candidates,
            settings=settings,
            client=active_client,
            diagnostics=diagnostics,
        )
        timeout_retests = run_timeout_retest_pass(
            fast_attempts,
            settings=settings,
            client=active_client,
            diagnostics=diagnostics,
        )
    finally:
        if owns_client:
            active_client.close()

    final_attempts = final_attempts_after_retests(fast_attempts, timeout_retests)
    reliability_rows = build_access_reliability_rows(final_attempts)
    optimization_status = determine_optimization_status(
        final_attempts,
        target_failure_rate=settings.target_failure_rate,
        requester_accepted_failures=requester_accepted_failures,
    )

    if optimization_status == OptimizationStatus.OPTIMIZE_AGAIN:
        diagnostics.append(
            log_runtime_diagnostic(
                LOGGER,
                logging.WARNING,
                "最终访问失败率超过阈值，需要继续优化。",
                {
                    "failure_rate": failure_rate(final_attempts),
                    "target_failure_rate": settings.target_failure_rate,
                },
            )
        )

    return ReachabilityResult(
        attempts=[*fast_attempts, *timeout_retests],
        final_attempts=final_attempts,
        reliability_rows=reliability_rows,
        optimization_status=optimization_status,
        diagnostics=diagnostics,
    )


def run_fast_reachability_pass(
    candidates: Sequence[CandidatePage],
    *,
    settings: RuntimeSettings,
    client: httpx.Client,
    diagnostics: list[str],
) -> list[TargetUrlAccessAttempt]:
    """Run the first full-scope reachability pass."""
    attempts: list[TargetUrlAccessAttempt] = []
    for candidate in candidates:
        attempts.append(
            check_target_url(
                candidate.target_url,
                stage=AccessStage.FAST_PASS,
                timeout_seconds=settings.fast_pass_timeout_seconds,
                client=client,
                diagnostics=diagnostics,
            )
        )
    return attempts


def run_timeout_retest_pass(
    fast_attempts: Sequence[TargetUrlAccessAttempt],
    *,
    settings: RuntimeSettings,
    client: httpx.Client,
    diagnostics: list[str],
) -> list[TargetUrlAccessAttempt]:
    """Retest only timeout failures with a more conservative timeout allowance."""
    retests: list[TargetUrlAccessAttempt] = []
    for attempt in fast_attempts:
        if attempt.failure_type != FailureType.TIMEOUT:
            continue
        diagnostics.append(
            log_runtime_diagnostic(
                LOGGER,
                logging.INFO,
                "正在重试超时目标网址。",
                {"url": attempt.target_url},
            )
        )
        retests.append(
            check_target_url(
                attempt.target_url,
                stage=AccessStage.TIMEOUT_RETEST,
                timeout_seconds=settings.timeout_retest_seconds,
                client=client,
                diagnostics=diagnostics,
                was_retested=True,
            )
        )
    return retests


def check_target_url(
    target_url: str,
    *,
    stage: AccessStage,
    timeout_seconds: float,
    client: httpx.Client,
    diagnostics: list[str],
    was_retested: bool = False,
) -> TargetUrlAccessAttempt:
    """Check a single target URL and classify the result."""
    started_at = monotonic()
    try:
        normalized_url = normalize_target_url(target_url)
    except UnsafeUrlError:
        return build_failure_attempt(
            target_url,
            stage=stage,
            failure_type=FailureType.INVALID_URL,
            elapsed_ms=0,
            was_retested=was_retested,
            diagnostics=diagnostics,
        )

    try:
        response = client.get(normalized_url, timeout=timeout_seconds)
    except httpx.TimeoutException:
        return build_failure_attempt(
            normalized_url,
            stage=stage,
            failure_type=FailureType.TIMEOUT,
            elapsed_ms=elapsed_ms_since(started_at),
            was_retested=was_retested,
            diagnostics=diagnostics,
        )
    except httpx.ConnectError:
        return build_failure_attempt(
            normalized_url,
            stage=stage,
            failure_type=FailureType.CONNECTION_FAILURE,
            elapsed_ms=elapsed_ms_since(started_at),
            was_retested=was_retested,
            diagnostics=diagnostics,
        )
    except httpx.HTTPError:
        return build_failure_attempt(
            normalized_url,
            stage=stage,
            failure_type=FailureType.CONNECTION_FAILURE,
            elapsed_ms=elapsed_ms_since(started_at),
            was_retested=was_retested,
            diagnostics=diagnostics,
        )

    elapsed_ms = elapsed_ms_since(started_at)
    failure_type = classify_response_failure(response, normalized_url)
    if failure_type != FailureType.NONE:
        return build_failure_attempt(
            normalized_url,
            stage=stage,
            failure_type=failure_type,
            status_code=response.status_code,
            elapsed_ms=elapsed_ms,
            was_retested=was_retested,
            diagnostics=diagnostics,
        )

    return TargetUrlAccessAttempt(
        target_url=normalized_url,
        stage=stage,
        outcome=AccessOutcome.SUCCESS,
        failure_type=FailureType.NONE,
        status_code=response.status_code,
        elapsed_ms=elapsed_ms,
        was_retested=was_retested,
        diagnostic_message="目标网址访问成功。",
    )


def classify_response_failure(response: httpx.Response, requested_url: str) -> FailureType:
    """Classify HTTP response failures."""
    if response.is_redirect:
        location = response.headers.get("location", "")
        if not location:
            return FailureType.REDIRECT_FAILURE
        requested_host = urlsplit(requested_url).hostname
        redirect_url = str(response.next_request.url) if response.next_request else location
        redirect_host = urlsplit(redirect_url).hostname
        if requested_host and redirect_host and requested_host != redirect_host:
            return FailureType.REDIRECT_FAILURE
        return FailureType.REDIRECT_FAILURE

    if response.status_code in {401, 403, 429}:
        return FailureType.BLOCKED_ACCESS
    if response.status_code >= 400:
        return FailureType.CONNECTION_FAILURE

    content_type = response.headers.get("content-type", "").lower()
    if content_type and not any(
        accepted_type in content_type
        for accepted_type in ("text/html", "text/plain", "application/xhtml+xml")
    ):
        return FailureType.UNSUPPORTED_CONTENT
    return FailureType.NONE


def build_failure_attempt(
    target_url: str,
    *,
    stage: AccessStage,
    failure_type: FailureType,
    elapsed_ms: int,
    diagnostics: list[str],
    status_code: int | None = None,
    was_retested: bool = False,
) -> TargetUrlAccessAttempt:
    """Build a failed access attempt and emit a Simplified Chinese diagnostic."""
    message = diagnostic_for_failure(failure_type)
    diagnostic = log_runtime_diagnostic(
        LOGGER,
        logging.WARNING,
        message,
        {"url": target_url, "failure_type": failure_type.value, "stage": stage.value},
    )
    diagnostics.append(diagnostic)
    return TargetUrlAccessAttempt(
        target_url=target_url,
        stage=stage,
        outcome=AccessOutcome.FAILURE,
        failure_type=failure_type,
        status_code=status_code,
        elapsed_ms=elapsed_ms,
        was_retested=was_retested,
        diagnostic_message=diagnostic,
    )


def diagnostic_for_failure(failure_type: FailureType) -> str:
    """Return a Simplified Chinese diagnostic for a failure category."""
    messages = {
        FailureType.TIMEOUT: "目标网址访问超时。",
        FailureType.CONNECTION_FAILURE: "目标网址连接失败。",
        FailureType.INVALID_URL: "目标网址无效或不安全。",
        FailureType.BLOCKED_ACCESS: "目标网址访问被阻止。",
        FailureType.REDIRECT_FAILURE: "目标网址重定向不符合要求。",
        FailureType.UNSUPPORTED_CONTENT: "目标网址内容类型不受支持。",
    }
    return messages.get(failure_type, "目标网址访问失败。")


def final_attempts_after_retests(
    fast_attempts: Sequence[TargetUrlAccessAttempt],
    timeout_retests: Sequence[TargetUrlAccessAttempt],
) -> list[TargetUrlAccessAttempt]:
    """Replace timeout fast-pass failures with their retest result."""
    retests_by_url = {attempt.target_url: attempt for attempt in timeout_retests}
    final_attempts: list[TargetUrlAccessAttempt] = []
    for attempt in fast_attempts:
        if attempt.failure_type == FailureType.TIMEOUT and attempt.target_url in retests_by_url:
            final_attempts.append(retests_by_url[attempt.target_url])
        else:
            final_attempts.append(attempt)
    return final_attempts


def build_access_reliability_rows(
    final_attempts: Sequence[TargetUrlAccessAttempt],
) -> list[AccessReliabilitySummary]:
    """Build spreadsheet-compatible reliability rows by failure type."""
    success_count = sum(1 for attempt in final_attempts if attempt.outcome == AccessOutcome.SUCCESS)
    failure_attempts = [
        attempt for attempt in final_attempts if attempt.outcome == AccessOutcome.FAILURE
    ]
    failure_count = len(failure_attempts)
    total_count = success_count + failure_count
    success_rate = percentage(success_count, total_count)
    final_failure_rate = percentage(failure_count, total_count)
    failure_counts = Counter(attempt.failure_type for attempt in failure_attempts)

    if not failure_counts:
        return [
            AccessReliabilitySummary(
                success_count=success_count,
                success_rate=success_rate,
                failure_count=0,
                failure_rate=0.0 if total_count else 0.0,
                failure_type=FailureType.NONE,
                failure_type_count=0,
            )
        ]

    return [
        AccessReliabilitySummary(
            success_count=success_count,
            success_rate=success_rate,
            failure_count=failure_count,
            failure_rate=final_failure_rate,
            failure_type=failure_type,
            failure_type_count=count,
        )
        for failure_type, count in sorted(failure_counts.items(), key=lambda item: item[0].value)
    ]


def determine_optimization_status(
    final_attempts: Sequence[TargetUrlAccessAttempt],
    *,
    target_failure_rate: float,
    requester_accepted_failures: bool,
) -> OptimizationStatus:
    """Determine whether the run is ready, accepted, or needs optimization."""
    if failure_rate(final_attempts) <= target_failure_rate:
        return OptimizationStatus.READY
    if requester_accepted_failures:
        return OptimizationStatus.ACCEPTED_BY_REQUESTER
    return OptimizationStatus.OPTIMIZE_AGAIN


def failure_rate(final_attempts: Sequence[TargetUrlAccessAttempt]) -> float:
    """Return final access failure rate as a 0.0-1.0 ratio."""
    if not final_attempts:
        return 0.0
    failure_count = sum(1 for attempt in final_attempts if attempt.outcome == AccessOutcome.FAILURE)
    return failure_count / len(final_attempts)


def percentage(count: int, total: int) -> float:
    """Return a rounded percentage."""
    if total == 0:
        return 0.0
    return round((count / total) * 100, 2)


def elapsed_ms_since(started_at: float) -> int:
    """Return elapsed milliseconds since a monotonic timestamp."""
    return max(0, round((monotonic() - started_at) * 1000))

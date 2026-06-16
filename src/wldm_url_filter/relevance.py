"""Keyword and semantic relevance filtering for discovered candidate pages."""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from rapidfuzz import fuzz

from wldm_url_filter.config import UnsafeUrlError, normalized_url_key
from wldm_url_filter.logging_config import log_runtime_diagnostic
from wldm_url_filter.models import (
    AcceptedUrlMatch,
    CandidatePage,
    MatchedSignal,
    MatchType,
    RelevanceDecision,
    TargetKeyword,
)

LOGGER = logging.getLogger(__name__)
UTILITY_EXCLUSION_PARTS = {
    "about",
    "account",
    "admin",
    "archive",
    "author",
    "cart",
    "category",
    "contact",
    "login",
    "privacy",
    "search",
    "signin",
    "signup",
    "tag",
    "terms",
}
SIGNAL_WEIGHTS = {
    MatchedSignal.URL_SLUG: 100,
    MatchedSignal.TITLE: 95,
    MatchedSignal.PRIMARY_HEADING: 92,
    MatchedSignal.CORE_METADATA: 85,
}
CLOSE_VARIANT_THRESHOLD = 84


@dataclass(frozen=True, slots=True)
class RelevanceResult:
    """Relevance decisions and accepted matches for a relevance run."""

    decisions: list[RelevanceDecision]
    accepted_matches: list[AcceptedUrlMatch]
    diagnostics: list[str]


@dataclass(frozen=True, slots=True)
class PrimarySignals:
    """Normalized primary signals used for relevance matching."""

    url_slug: str
    title: str
    primary_heading: str
    core_metadata: str


@dataclass(frozen=True, slots=True)
class KeywordMatch:
    """Strongest keyword evidence found in one signal."""

    keyword: TargetKeyword
    matched_signal: MatchedSignal
    match_type: MatchType
    relevance_score: int


def filter_relevant_candidates(
    candidates: Sequence[CandidatePage],
    target_keywords: Sequence[TargetKeyword],
) -> RelevanceResult:
    """Evaluate candidate pages and return accepted matches with strongest evidence."""
    diagnostics: list[str] = []
    decisions: list[RelevanceDecision] = []
    for candidate in candidates:
        decision = evaluate_candidate_relevance(candidate, target_keywords)
        decisions.append(decision)
        if decision.matched:
            diagnostics.append(
                log_runtime_diagnostic(
                    LOGGER,
                    logging.INFO,
                    "候选页面匹配目标关键词。",
                    {
                        "url": candidate.target_url,
                        "keyword": decision.detected_keyword,
                        "score": decision.relevance_score,
                    },
                )
            )
        else:
            diagnostics.append(
                log_runtime_diagnostic(
                    LOGGER,
                    logging.INFO,
                    "候选页面未通过相关性过滤。",
                    {"url": candidate.target_url, "reason": decision.exclusion_reason},
                )
            )

    strongest_decisions = strongest_decisions_by_url(decisions, candidates)
    accepted_matches = [
        AcceptedUrlMatch(
            source_domain=candidate.source_domain,
            target_url=decision.target_url,
            detected_keyword=decision.detected_keyword or "",
            relevance_score=decision.relevance_score,
        )
        for decision, candidate in strongest_decisions
        if decision.matched
    ]
    return RelevanceResult(
        decisions=decisions,
        accepted_matches=accepted_matches,
        diagnostics=diagnostics,
    )


def evaluate_candidate_relevance(
    candidate: CandidatePage,
    target_keywords: Sequence[TargetKeyword],
) -> RelevanceDecision:
    """Evaluate one candidate against target keywords and utility exclusions."""
    utility_reason = utility_exclusion_reason(candidate)
    if utility_reason:
        return RelevanceDecision(
            target_url=candidate.target_url,
            matched=False,
            relevance_score=0,
            exclusion_reason=utility_reason,
        )

    signals = extract_primary_signals(candidate)
    match = strongest_keyword_match(signals, target_keywords)
    if match is None:
        return RelevanceDecision(
            target_url=candidate.target_url,
            matched=False,
            relevance_score=0,
            exclusion_reason="no_primary_signal_match",
        )

    return RelevanceDecision(
        target_url=candidate.target_url,
        matched=True,
        detected_keyword=match.keyword.keyword,
        matched_signal=match.matched_signal,
        match_type=match.match_type,
        relevance_score=match.relevance_score,
    )


def extract_primary_signals(candidate: CandidatePage) -> PrimarySignals:
    """Normalize primary page signals used for keyword evidence."""
    return PrimarySignals(
        url_slug=normalize_signal(candidate.url_slug),
        title=normalize_signal(candidate.title),
        primary_heading=normalize_signal(candidate.primary_heading),
        core_metadata=normalize_signal(candidate.core_metadata),
    )


def strongest_keyword_match(
    signals: PrimarySignals,
    target_keywords: Sequence[TargetKeyword],
) -> KeywordMatch | None:
    """Return the strongest exact or close-variant keyword evidence."""
    matches: list[KeywordMatch] = []
    signal_values = {
        MatchedSignal.URL_SLUG: signals.url_slug,
        MatchedSignal.TITLE: signals.title,
        MatchedSignal.PRIMARY_HEADING: signals.primary_heading,
        MatchedSignal.CORE_METADATA: signals.core_metadata,
    }
    for keyword in target_keywords:
        keyword_value = normalize_signal(keyword.normalized_keyword)
        if not keyword_value:
            continue
        for signal, value in signal_values.items():
            if not value:
                continue
            exact_score = exact_keyword_score(keyword_value, value, signal)
            if exact_score:
                matches.append(
                    KeywordMatch(
                        keyword=keyword,
                        matched_signal=signal,
                        match_type=MatchType.EXACT_KEYWORD,
                        relevance_score=exact_score,
                    )
                )
                continue
            close_score = close_variant_score(keyword_value, value, signal)
            if close_score:
                matches.append(
                    KeywordMatch(
                        keyword=keyword,
                        matched_signal=signal,
                        match_type=MatchType.CLOSE_SEMANTIC_VARIANT,
                        relevance_score=close_score,
                    )
                )

    if not matches:
        return None
    return max(matches, key=lambda match: match.relevance_score)


def exact_keyword_score(keyword: str, signal_value: str, signal: MatchedSignal) -> int:
    """Return exact keyword score for a primary signal."""
    if keyword == signal_value or keyword in signal_value:
        return SIGNAL_WEIGHTS[signal]
    return 0


def close_variant_score(keyword: str, signal_value: str, signal: MatchedSignal) -> int:
    """Return close lexical variant score for a primary signal."""
    best_score = max(
        fuzz.partial_ratio(keyword, signal_value),
        fuzz.token_set_ratio(keyword, signal_value),
    )
    if best_score < CLOSE_VARIANT_THRESHOLD:
        return 0
    weighted_score = round(SIGNAL_WEIGHTS[signal] * (best_score / 100) - 5)
    return max(1, min(99, weighted_score))


def utility_exclusion_reason(candidate: CandidatePage) -> str:
    """Return exclusion reason when a candidate is a utility page."""
    if candidate.utility_page_flag:
        return "utility_page"
    path_terms = set(normalize_signal(candidate.url_slug).split())
    if path_terms.intersection(UTILITY_EXCLUSION_PARTS):
        return "utility_page"
    return ""


def strongest_decisions_by_url(
    decisions: Sequence[RelevanceDecision],
    candidates: Sequence[CandidatePage],
) -> list[tuple[RelevanceDecision, CandidatePage]]:
    """Preserve the strongest relevance decision for duplicate target URLs."""
    candidates_by_url = {candidate.target_url: candidate for candidate in candidates}
    strongest: dict[str, tuple[RelevanceDecision, CandidatePage]] = {}
    for decision in decisions:
        candidate = candidates_by_url.get(decision.target_url)
        if candidate is None:
            continue
        try:
            key = normalized_url_key(decision.target_url, allowed_domain=candidate.source_domain)
        except UnsafeUrlError:
            key = decision.target_url
        current = strongest.get(key)
        if current is None or decision.relevance_score > current[0].relevance_score:
            strongest[key] = (decision, candidate)
    return list(strongest.values())


def normalize_signal(value: str) -> str:
    """Normalize a page signal for keyword matching."""
    lowered = value.lower()
    lowered = re.sub(r"[^a-z0-9]+", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def accepted_urls_from_candidates(
    candidates: Iterable[CandidatePage],
    target_keywords: Sequence[TargetKeyword],
) -> list[AcceptedUrlMatch]:
    """Convenience helper for tests and later output phases."""
    return filter_relevant_candidates(list(candidates), target_keywords).accepted_matches

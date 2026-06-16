"""Shared data models for the URL discovery pipeline."""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ValidationStatus(StrEnum):
    """Input record validation status."""

    VALID = "valid"
    DUPLICATE = "duplicate"
    INVALID = "invalid"


class DiscoverySource(StrEnum):
    """Source used to discover a candidate page."""

    HOMEPAGE = "homepage"
    INTERNAL_LINK = "internal_link"
    SITEMAP = "sitemap"
    METADATA = "metadata"


class AccessStage(StrEnum):
    """Reachability check stage."""

    FAST_PASS = "fast_pass"
    TIMEOUT_RETEST = "timeout_retest"


class AccessOutcome(StrEnum):
    """Reachability outcome."""

    SUCCESS = "success"
    FAILURE = "failure"


class FailureType(StrEnum):
    """Reachability failure category."""

    TIMEOUT = "timeout"
    CONNECTION_FAILURE = "connection_failure"
    INVALID_URL = "invalid_url"
    BLOCKED_ACCESS = "blocked_access"
    REDIRECT_FAILURE = "redirect_failure"
    UNSUPPORTED_CONTENT = "unsupported_content"
    NONE = "none"


class MatchedSignal(StrEnum):
    """Primary page signal that produced the strongest match."""

    URL_SLUG = "url_slug"
    TITLE = "title"
    PRIMARY_HEADING = "primary_heading"
    CORE_METADATA = "core_metadata"


class MatchType(StrEnum):
    """Relevance match category."""

    EXACT_KEYWORD = "exact_keyword"
    CLOSE_SEMANTIC_VARIANT = "close_semantic_variant"


class OptimizationStatus(StrEnum):
    """Run readiness status."""

    READY = "ready"
    OPTIMIZE_AGAIN = "optimize_again"
    ACCEPTED_BY_REQUESTER = "accepted_by_requester"


class StrictModel(BaseModel):
    """Base model settings shared by pipeline entities."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SourceDomain(StrictModel):
    """One root-domain input record after validation."""

    raw_value: str
    normalized_domain: str | None = None
    input_row_number: int = Field(ge=1)
    validation_status: ValidationStatus
    validation_reason: str = ""

    @model_validator(mode="after")
    def validate_domain_state(self) -> Self:
        """Ensure status fields agree with the normalized domain."""
        if self.validation_status == ValidationStatus.VALID and not self.normalized_domain:
            raise ValueError("valid source domains require normalized_domain")
        if self.validation_status != ValidationStatus.VALID and not self.validation_reason:
            raise ValueError("invalid or duplicate source domains require validation_reason")
        return self


class TargetKeyword(StrictModel):
    """One normalized target keyword."""

    keyword: str = Field(min_length=1)
    normalized_keyword: str = Field(min_length=1)
    keyword_group: str | None = None


class CandidatePage(StrictModel):
    """A discovered page before final relevance filtering."""

    source_domain: str = Field(min_length=1)
    target_url: str = Field(min_length=1)
    discovery_source: DiscoverySource
    url_slug: str = ""
    title: str = ""
    primary_heading: str = ""
    core_metadata: str = ""
    utility_page_flag: bool = False


class DiscoveryScope(StrictModel):
    """Crawl-depth decision for a single source domain."""

    source_domain: str = Field(min_length=1)
    initial_depth: int = Field(default=2, ge=2, le=2)
    expanded_depth: int | None = None
    min_recall_sample_count: int = Field(ge=1)
    depth_2_candidate_count: int = Field(ge=0)
    expanded_to_depth_3: bool
    final_candidate_count: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_depth_state(self) -> Self:
        """Ensure adaptive depth fields preserve the phase contract."""
        if self.expanded_to_depth_3:
            if self.expanded_depth != 3:
                raise ValueError("expanded scopes require expanded_depth=3")
            if self.depth_2_candidate_count >= self.min_recall_sample_count:
                raise ValueError(
                    "scope must not expand when depth-2 recall already meets the threshold"
                )
        elif self.expanded_depth is not None:
            raise ValueError("expanded_depth must be empty when expanded_to_depth_3 is false")
        if self.final_candidate_count < self.depth_2_candidate_count:
            raise ValueError("final_candidate_count cannot be lower than depth_2_candidate_count")
        return self


class TargetUrlAccessAttempt(StrictModel):
    """One reachability attempt for a target URL."""

    target_url: str = Field(min_length=1)
    stage: AccessStage
    outcome: AccessOutcome
    failure_type: FailureType = FailureType.NONE
    status_code: int | None = Field(default=None, ge=100, le=599)
    elapsed_ms: int = Field(ge=0)
    was_retested: bool = False
    diagnostic_message: str = ""

    @model_validator(mode="after")
    def validate_attempt_state(self) -> Self:
        """Ensure success and failure fields do not contradict each other."""
        if self.outcome == AccessOutcome.SUCCESS and self.failure_type != FailureType.NONE:
            raise ValueError("successful access attempts must use failure_type=none")
        if self.outcome == AccessOutcome.FAILURE and self.failure_type == FailureType.NONE:
            raise ValueError("failed access attempts require a concrete failure_type")
        return self


class RelevanceDecision(StrictModel):
    """Page-level relevance decision."""

    target_url: str = Field(min_length=1)
    matched: bool
    detected_keyword: str | None = None
    matched_signal: MatchedSignal | None = None
    match_type: MatchType | None = None
    relevance_score: int = Field(ge=0, le=100)
    exclusion_reason: str = ""

    @model_validator(mode="after")
    def validate_relevance_state(self) -> Self:
        """Ensure accepted decisions contain evidence."""
        if self.matched:
            if not self.detected_keyword or self.matched_signal is None or self.match_type is None:
                raise ValueError(
                    "matched relevance decisions require keyword, signal, and match_type"
                )
            if self.relevance_score == 0:
                raise ValueError("matched relevance decisions require a positive score")
        return self


class AcceptedUrlMatch(StrictModel):
    """One row in the final accepted URL output."""

    source_domain: str = Field(min_length=1)
    target_url: str = Field(min_length=1)
    detected_keyword: str = Field(min_length=1)
    relevance_score: int = Field(ge=0, le=100)


class AccessReliabilitySummary(StrictModel):
    """Spreadsheet-compatible reliability summary row."""

    success_count: int = Field(ge=0)
    success_rate: float = Field(ge=0, le=100)
    failure_count: int = Field(ge=0)
    failure_rate: float = Field(ge=0, le=100)
    failure_type: FailureType
    failure_type_count: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_rate_state(self) -> Self:
        """Ensure success and failure rates represent a complete population."""
        if (
            self.success_count + self.failure_count > 0
            and abs((self.success_rate + self.failure_rate) - 100.0) > 0.1
        ):
            raise ValueError("success_rate plus failure_rate must equal 100")
        return self


class ProcessingSummary(StrictModel):
    """Run-level review and coverage summary."""

    total_input_rows: int = Field(ge=0)
    valid_domains: int = Field(ge=0)
    invalid_domains: int = Field(ge=0)
    duplicate_domains: int = Field(ge=0)
    domains_attempted: int = Field(ge=0)
    domains_with_matches: int = Field(ge=0)
    accepted_url_count: int = Field(ge=0)
    excluded_candidate_count: int = Field(ge=0)
    inaccessible_domain_count: int = Field(ge=0)
    optimization_status: OptimizationStatus

    @model_validator(mode="after")
    def validate_summary_state(self) -> Self:
        """Ensure summary counts are internally consistent."""
        classified_rows = self.valid_domains + self.invalid_domains + self.duplicate_domains
        if classified_rows != self.total_input_rows:
            raise ValueError("domain classifications must equal total_input_rows")
        if self.domains_attempted > self.valid_domains:
            raise ValueError("domains_attempted cannot exceed valid_domains")
        if self.domains_with_matches > self.domains_attempted:
            raise ValueError("domains_with_matches cannot exceed domains_attempted")
        if self.accepted_url_count < self.domains_with_matches:
            raise ValueError("accepted_url_count cannot be lower than domains_with_matches")
        if self.inaccessible_domain_count > self.domains_attempted:
            raise ValueError("inaccessible_domain_count cannot exceed domains_attempted")
        return self

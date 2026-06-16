# Data Model: Automated URL Discovery and Semantic Relevance Filter

## SourceDomain

Represents one root-domain input record after ingestion.

**Fields**:
- `raw_value`: Original input cell value.
- `normalized_domain`: Canonical root domain used for processing.
- `input_row_number`: Source row number for traceability.
- `validation_status`: `valid`, `duplicate`, or `invalid`.
- `validation_reason`: Human-readable reason for invalid or duplicate records.

**Validation rules**:
- Blank values are invalid.
- Protocols, paths, casing, and trailing slashes are normalized before duplicate detection.
- Private, local, or unsafe hostnames are invalid for network access.

## TargetKeyword

Represents one niche relevance term.

**Fields**:
- `keyword`: Original keyword text.
- `normalized_keyword`: Canonical keyword used for matching.
- `keyword_group`: Optional grouping when the input provides categories.

**Validation rules**:
- Blank keywords are ignored.
- Duplicate normalized keywords are collapsed.

## CandidatePage

Represents a discovered page before final relevance filtering.

**Fields**:
- `source_domain`: Link to `SourceDomain.normalized_domain`.
- `target_url`: Absolute discovered URL.
- `discovery_source`: `homepage`, `internal_link`, `sitemap`, or `metadata`.
- `url_slug`: URL path terms used for relevance evidence.
- `title`: Page title text when available.
- `primary_heading`: Primary heading text when available.
- `core_metadata`: Description, canonical URL, or other core metadata text.
- `utility_page_flag`: Whether the page matches utility-page exclusion patterns.

**Validation rules**:
- Target URL must remain within the source domain or an accepted redirect target.
- Utility pages are excluded before accepted match export.
- Duplicate or equivalent target URLs are normalized before scoring.

## DiscoveryScope

Represents the crawl-depth decision for one source domain or target URL discovery scope.

**Fields**:
- `source_domain`: Link to `SourceDomain.normalized_domain`.
- `initial_depth`: Starting crawl depth, fixed at `2`.
- `expanded_depth`: Optional fallback crawl depth, fixed at `3` when expansion is triggered.
- `min_recall_sample_count`: Configured minimum candidate count N required before skipping expansion.
- `depth_2_candidate_count`: Candidate count discovered before any depth expansion.
- `expanded_to_depth_3`: Whether the scope expanded after the depth-2 pass.
- `final_candidate_count`: Candidate count after optional expansion and deduplication.

**Validation rules**:
- Discovery starts at depth 2 for every scope.
- A scope expands to depth 3 only when `depth_2_candidate_count` is less than `min_recall_sample_count`.
- A scope must not expand to depth 3 when `depth_2_candidate_count` is greater than or equal to
  `min_recall_sample_count`.
- Candidate-page and utility-page filters still apply after depth expansion.

## TargetUrlAccessAttempt

Represents one reachability check for a target URL.

**Fields**:
- `target_url`: URL being checked.
- `stage`: `fast_pass` or `timeout_retest`.
- `outcome`: `success` or `failure`.
- `failure_type`: `timeout`, `connection_failure`, `invalid_url`, `blocked_access`, `redirect_failure`,
  `unsupported_content`, or `none`.
- `status_code`: HTTP status code when available.
- `elapsed_ms`: Observed access duration.
- `was_retested`: Whether the URL was included in the timeout-only retest pass.
- `diagnostic_message`: Simplified Chinese runtime diagnostic message for logs and run reports.

**State transitions**:
- `fast_pass` timeout -> `timeout_retest`.
- `timeout_retest` success -> final `success`.
- `timeout_retest` failure -> final `failure` with failure type.
- Non-timeout `fast_pass` failures remain final unless classified as retryable by future optimization.

## RelevanceDecision

Represents the page-level relevance evaluation for a candidate page.

**Fields**:
- `target_url`: Candidate page URL.
- `matched`: Boolean decision.
- `detected_keyword`: Keyword that triggered the strongest match.
- `matched_signal`: `url_slug`, `title`, `primary_heading`, or `core_metadata`.
- `match_type`: `exact_keyword` or `close_semantic_variant`.
- `relevance_score`: Numeric confidence score from 0 to 100.
- `exclusion_reason`: Reason when the page is rejected.

**Validation rules**:
- A page is accepted only when at least one primary page signal clearly matches an exact target keyword or close
  semantic variant.
- Utility-page exclusions override incidental keyword evidence.
- When duplicate target URLs exist, the strongest relevance decision is preserved.

## AcceptedUrlMatch

Represents one row in the final accepted spreadsheet.

**Fields**:
- `source_domain`: Source domain that led to the accepted URL.
- `target_url`: Deep URL that passed access and relevance filtering.
- `detected_keyword`: Keyword that triggered the match.
- `relevance_score`: Confidence score from 0 to 100.

**Validation rules**:
- All fields are required.
- `target_url` must be unique in the final spreadsheet.
- Homepage URLs are included only when the homepage itself clearly satisfies relevance rules.

## AccessReliabilitySummary

Represents the additional spreadsheet-compatible reliability table.

**Fields**:
- `success_count`: Number of final successful target URL access attempts.
- `success_rate`: Percentage of valid target URL access attempts that succeeded.
- `failure_count`: Number of final failed target URL access attempts.
- `failure_rate`: Percentage of valid target URL access attempts that failed.
- `failure_type`: Failure category.
- `failure_type_count`: Count for the failure category.

**Validation rules**:
- Success rate plus failure rate must equal 100% after rounding tolerance.
- Failure rate is calculated after timeout retesting.
- If failure rate is greater than 10%, the run remains not ready unless the requester explicitly accepts the
  documented remaining failures.

## ProcessingSummary

Represents run-level review information.

**Fields**:
- `total_input_rows`: Number of rows read from the domain input file.
- `valid_domains`: Number of valid unique domains.
- `invalid_domains`: Number of invalid domains.
- `duplicate_domains`: Number of duplicate domains.
- `domains_attempted`: Number of valid domains attempted.
- `domains_with_matches`: Number of domains with at least one accepted URL.
- `accepted_url_count`: Number of accepted URL matches.
- `excluded_candidate_count`: Number of rejected candidate pages.
- `inaccessible_domain_count`: Number of domains that could not be accessed or interpreted.
- `optimization_status`: `ready`, `optimize_again`, or `accepted_by_requester`.

**Validation rules**:
- Counts must be internally consistent with input, access attempts, and accepted output rows.
- `optimization_status` is `optimize_again` when access failure rate is greater than 10% and no requester
  acceptance has been recorded.

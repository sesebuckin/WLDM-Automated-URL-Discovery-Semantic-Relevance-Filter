# Feature Specification: Automated URL Discovery and Semantic Relevance Filter

**Feature Branch**: N/A (no branch creation hook configured)

**Created**: 2026-06-16

**Status**: Draft

**Input**: User description: "Process a noisy list of approximately 3,000 root domains and a keyword list to discover relevant deep pages, filter them by semantic relevance, and generate a clean spreadsheet of matching URLs."

**Language Requirement**: This specification and all downstream project documents MUST be written in English.

## Clarifications

### Session 2026-06-16

- Q: What should happen when the final access failure rate remains greater than 10% after the two-stage reachability process? → A: Continue optimization until the failure rate is <=10% or the requester explicitly accepts the remaining failures.
- Q: What match threshold should qualify a discovered page as semantically relevant? → A: Accept exact keywords or close semantic variants when at least one primary page signal clearly matches.
- Q: How should crawl depth balance precision and recall? → A: Start each domain or target URL discovery scope at depth 2; expand to depth 3 only when the depth-2 search returns fewer than the configured minimum recall sample count N.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Discover Candidate Deep Pages (Priority: P1)

As a project analyst, I want to start from a noisy list of root domains and discover specific article, guide, review, or other deep-content pages so that the final results are more granular than homepage URLs.

**Why this priority**: The challenge is only valuable if the workflow expands root domains into specific relevant pages rather than returning the original homepage list.

**Independent Test**: Provide a sample domain list containing at least one relevant site with deep pages and one junk site. Verify that the output candidates include deep URLs from the relevant site and exclude homepage-only results when no relevant deep page is found.

**Acceptance Scenarios**:

1. **Given** a root domain with pages whose URL slug, page title, or primary heading indicates topical relevance, **When** the workflow processes the domain, **Then** it records the relevant deep pages as candidates.
2. **Given** a root domain with only generic pages or no discoverable relevant content, **When** the workflow processes the domain, **Then** it does not emit the homepage as a match unless the homepage itself clearly satisfies the relevance rules.
3. **Given** depth-2 discovery returns at least the configured minimum recall sample count N for a domain or target URL scope, **When** the workflow evaluates whether to expand crawling, **Then** it does not expand that scope to depth 3.
4. **Given** depth-2 discovery returns fewer than the configured minimum recall sample count N for a domain or target URL scope, **When** the workflow evaluates recall coverage, **Then** it expands that scope to depth 3 before final candidate selection.

---

### User Story 2 - Minimize Target URL Access Failures (Priority: P1)

As a project analyst, I want target URL access checked through a two-stage reachability process so that timeout-sensitive sites get a second chance and the final failure rate is minimized.

**Why this priority**: Access failures directly reduce coverage and can hide relevant pages, so minimizing failures is required before relevance filtering can be trusted.

**Independent Test**: Provide a sample set containing clearly reachable URLs, timeout-prone URLs, invalid URLs, and blocked URLs. Verify that the workflow first completes a broad fast reachability pass, then retests timeout cases under more conservative access conditions, and reports the final success and failure rates.

**Acceptance Scenarios**:

1. **Given** a set of target URLs, **When** the workflow starts reachability detection, **Then** it performs an initial fast full-scope pass to identify obviously reachable URLs.
2. **Given** URLs that fail due to timeout in the first pass, **When** the second pass runs, **Then** only timeout cases are retested with lower or no concurrency and longer timeout allowance, based on whichever option produces the best observed access result.
3. **Given** reachability detection is complete, **When** the reviewer opens the access reliability output, **Then** it shows success count and percentage, failure count and percentage, each failure type, and the count for each failure type.
4. **Given** the final failure rate remains greater than 10%, **When** the run is reviewed, **Then** the workflow is not considered ready and optimization continues until the failure rate is 10% or lower or the requester explicitly accepts the remaining failures.

---

### User Story 3 - Filter Pages by Keyword and Semantic Relevance (Priority: P1)

As a reviewer, I want discovered pages scored against the target keyword list so that irrelevant utility pages, junk sites, and off-topic content are removed before delivery.

**Why this priority**: Precision is a primary success metric, and irrelevant pages reduce the usefulness of the delivered spreadsheet.

**Independent Test**: Provide candidate pages containing a mix of exact keyword matches, close semantic variants, utility pages, and off-topic content. Verify that the matching pages are retained with detected keywords and non-matching pages are discarded.

**Acceptance Scenarios**:

1. **Given** a candidate page whose URL slug, title, heading, or core metadata clearly contains a target keyword or close semantic variant, **When** the page is evaluated, **Then** it is marked as a match with the detected keyword and confidence information.
2. **Given** a utility page such as an about, contact, privacy, terms, login, category index, or generic navigation page, **When** the page is evaluated, **Then** it is excluded even if incidental text appears near a target keyword.
3. **Given** a candidate page from an unrelated junk domain, **When** it does not match the target niche, **Then** it is excluded from the final spreadsheet.

---

### User Story 4 - Deliver a Clean Spreadsheet (Priority: P2)

As the client-facing owner, I want a clean spreadsheet of only accepted URLs with clear evidence for each match so that I can review, share, and submit the results confidently.

**Why this priority**: The final deliverable must be easy to inspect and must show why each URL was selected.

**Independent Test**: Run the workflow on a representative sample and verify that the spreadsheet contains only accepted records and includes the required columns in the expected order.

**Acceptance Scenarios**:

1. **Given** accepted page matches, **When** the output is generated, **Then** each row includes Source Domain, Target URL, Detected Keyword, and Relevance Score.
2. **Given** no accepted pages for a source domain, **When** the output is generated, **Then** the domain is omitted from the final spreadsheet.
3. **Given** duplicate target URLs or equivalent normalized URLs, **When** the output is generated, **Then** duplicate rows are removed while preserving the strongest relevance evidence.

---

### User Story 5 - Review Processing Coverage and Exclusions (Priority: P3)

As a project analyst, I want a concise processing summary so that I can understand how many domains were reviewed, how many produced matches, and why common exclusions occurred.

**Why this priority**: The challenge emphasizes precision and noisy input; a summary helps validate that the workflow handled the input set rather than silently skipping large portions.

**Independent Test**: Process a sample dataset with known relevant, irrelevant, duplicate, and inaccessible domains. Verify that the summary reports totals for processed domains, matched domains, accepted URLs, exclusions, duplicates, and inaccessible domains.

**Acceptance Scenarios**:

1. **Given** a completed run, **When** the reviewer opens the processing summary, **Then** it reports total input domains, domains attempted, domains with matches, accepted target URLs, and excluded candidate pages.
2. **Given** domains that cannot be accessed or interpreted, **When** processing completes, **Then** those domains are summarized separately from domains that were accessed but found irrelevant.

### Edge Cases

- Input files contain blank rows, malformed domains, duplicate domains, mixed protocols, trailing paths, or inconsistent casing.
- A domain redirects to another domain, blocks access, times out, or returns only non-content pages.
- A site contains many pages whose navigation text includes a target keyword but whose individual pages are utility pages or off-topic content.
- A target keyword appears only in boilerplate, footer text, advertisements, tags, or unrelated navigation.
- Multiple target keywords match the same target URL.
- The same deep page is discovered through multiple paths or URL variants.
- A page has no title, no primary heading, or incomplete metadata.
- A URL fails during fast access but succeeds when timeout cases are retested under more conservative access conditions.
- The final access failure rate remains greater than 10% after timeout retesting.
- Runtime failures or operational messages must be emitted in Simplified Chinese and must not expose sensitive data.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept a domain input dataset containing approximately 3,000 root domains, including noisy, duplicate, malformed, and irrelevant entries.
- **FR-002**: System MUST accept a target keyword dataset that defines the niche relevance criteria for the run.
- **FR-003**: System MUST normalize source domains sufficiently to avoid duplicate processing caused by protocol, casing, trailing slash, or equivalent root-domain formatting differences.
- **FR-004**: System MUST attempt to discover deep candidate pages from each valid source domain rather than relying only on the homepage.
- **FR-005**: System MUST prioritize candidate pages whose URL slug, page title, primary heading, or core metadata suggests relevance to the target keyword dataset.
- **FR-005a**: System MUST initialize discovery depth at 2 for each domain or target URL scope, and MUST expand that scope to depth 3 only when the depth-2 search returns fewer than the configured minimum recall sample count N.
- **FR-006**: System MUST exclude common utility and administrative pages, including about, contact, privacy, terms, login, account, tag index, category index, and generic navigation pages.
- **FR-007**: System MUST evaluate candidate pages against target keywords and close semantic variants using primary page signals: URL slug, title, primary heading, and core metadata.
- **FR-008**: System MUST retain a page only when at least one primary page signal clearly matches an exact target keyword or close semantic variant.
- **FR-009**: System MUST record the source domain, target URL, detected keyword, and relevance score for every accepted page.
- **FR-010**: System MUST remove duplicate target URLs and preserve the row with the strongest relevance evidence when duplicates occur.
- **FR-011**: System MUST omit domains and pages that do not pass the relevance filter from the final spreadsheet.
- **FR-012**: System MUST generate a spreadsheet-compatible output containing only accepted URLs and the required columns in this order: Source Domain, Target URL, Detected Keyword, Relevance Score.
- **FR-013**: System SHOULD generate a processing summary that reports domain coverage, accepted URL count, exclusion categories, duplicates, and inaccessible domains.
- **FR-014**: System MUST emit runtime error messages and log messages in Simplified Chinese for operational failures, exclusions, and run summaries.
- **FR-015**: System MUST NOT include secrets, passwords, tokens, cookies, or sensitive credentials in source content, output files, logs, or diagnostic messages.
- **FR-016**: System MUST evaluate target URL reachability through two stages: an initial fast full-scope pass for clearly reachable targets, followed by a timeout-only retest pass.
- **FR-017**: System MUST retest first-pass timeout cases with lower or no concurrency and a longer timeout allowance, choosing the option that best minimizes final access failures.
- **FR-018**: System MUST classify final access failures by failure type, including at minimum timeout, connection failure, invalid URL, blocked access, redirect failure, and unsupported content.
- **FR-019**: System MUST generate an additional spreadsheet-compatible access reliability table with these columns: Success Count, Success Rate, Failure Count, Failure Rate, Failure Type, Failure Type Count.
- **FR-020**: System MUST calculate the final access failure rate after timeout retesting and mark the run as not ready when the final failure rate is greater than 10%.
- **FR-021**: When the final access failure rate is greater than 10%, the workflow MUST continue optimization and provide the remaining failure breakdown and recommended discussion points until the failure rate is 10% or lower or the requester explicitly accepts the remaining failures.

### Key Entities *(include if feature involves data)*

- **Source Domain**: A root-domain input record to be normalized, validated, and processed for candidate page discovery.
- **Target Keyword**: A niche relevance term used to identify exact and semantically close page matches.
- **Candidate Page**: A discovered page associated with a source domain before final relevance filtering.
- **Accepted URL Match**: A candidate page that passes exclusion and relevance rules and appears in the final spreadsheet.
- **Target URL Access Attempt**: A reachability check for a target URL, including stage, outcome, failure type, and whether the URL was retested after timeout.
- **Access Reliability Summary**: A spreadsheet-compatible table that reports success and failure counts, rates, failure types, and counts per failure type.
- **Processing Summary**: Run-level information about coverage, matches, exclusions, duplicates, and inaccessible domains.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least 95% of valid input domains in a representative sample are attempted and reported as matched, unmatched, duplicate, invalid, or inaccessible.
- **SC-002**: At least 90% of accepted rows in a manually reviewed sample are relevant to at least one target keyword or close semantic variant.
- **SC-003**: At least 90% of accepted rows contain a deep target URL rather than only the source homepage.
- **SC-004**: 100% of final spreadsheet rows include non-empty Source Domain, Target URL, Detected Keyword, and Relevance Score values.
- **SC-005**: 100% of common utility pages identified in the representative sample are excluded from the final spreadsheet.
- **SC-006**: Duplicate target URLs do not appear more than once in the final spreadsheet.
- **SC-007**: A reviewer can understand why each accepted URL was included by inspecting the Detected Keyword and Relevance Score columns.
- **SC-008**: 100% of first-pass timeout failures are either retested in the second pass or reported with a reason why retesting was not possible.
- **SC-009**: The final access reliability output includes success count, success rate, failure count, failure rate, failure type, and failure type count.
- **SC-010**: The final access failure rate is 10% or lower for the representative sample, or the requester explicitly accepts the documented remaining failures after continued optimization discussion.

## Assumptions

- The domain dataset and target keyword dataset are provided as spreadsheet-compatible files with recognizable column content.
- Relevance is determined primarily from page-level signals such as URL slug, title, primary heading, and core metadata, not from unrelated boilerplate.
- The workflow is expected to process a provided sample dataset for the deliverable and should be able to scale to approximately 3,000 input domains.
- Inaccessible or blocking domains are acceptable as long as they are tracked separately and do not produce false-positive accepted URLs.
- Access failure rate is calculated over valid target URL access attempts after the second-stage timeout retest; malformed and duplicate inputs are reported separately.
- Timeout retesting focuses only on timeout failures from the first pass, while clearly invalid, blocked, or unsupported targets remain classified by their final failure type.
- The final machine-readable deliverable is a clean spreadsheet-compatible file; any separate submission packaging or email response is outside the processing workflow unless requested later.

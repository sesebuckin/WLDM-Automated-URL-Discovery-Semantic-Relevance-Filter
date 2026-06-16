---

description: "Task list for Automated URL Discovery and Semantic Relevance Filter"
---

# Tasks: Automated URL Discovery and Semantic Relevance Filter

**Input**: Design documents from `specs/001-url-discovery-filter/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/cli.md`, `quickstart.md`

**Tests**: Required by the project constitution. New behavior must include automated tests and unit test coverage
greater than 80%.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel after dependencies are met because it touches different files
- **[Story]**: Which user story the task belongs to
- All descriptions include exact file paths
- Task descriptions, documentation, comments, and commit-message guidance must be written in English

## Path Conventions

- Source code: `src/wldm_url_filter/`
- Tests: `tests/unit/`, `tests/integration/`, `tests/contract/`
- Sample input and generated output: `data/input/`, `data/output/`
- Feature docs: `specs/001-url-discovery-filter/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize the conda-restricted Python CLI project structure and quality gates.

- [X] T001 Verify the dedicated conda environment definition in `environment.yml`
- [X] T002 Create Python package metadata and console entry point in `pyproject.toml`
- [X] T003 Create the package initializer in `src/wldm_url_filter/__init__.py`
- [X] T004 Create the CLI application skeleton in `src/wldm_url_filter/cli.py`
- [X] T005 [P] Create the runtime configuration skeleton in `src/wldm_url_filter/config.py`
- [X] T006 [P] Create the logging configuration skeleton in `src/wldm_url_filter/logging_config.py`
- [X] T007 [P] Create test package placeholders in `tests/unit/__init__.py`, `tests/integration/__init__.py`, and `tests/contract/__init__.py`
- [X] T008 [P] Configure pytest and coverage defaults in `pyproject.toml`
- [X] T009 [P] Verify generated outputs, logs, caches, and local environments are ignored in `.gitignore`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Complete shared models, validation, security, diagnostics, and CLI contract foundations.

**Critical Requirement**: No user story implementation can begin until this phase is complete.

- [X] T010 Define SourceDomain, TargetKeyword, CandidatePage, DiscoveryScope, TargetUrlAccessAttempt, RelevanceDecision, AcceptedUrlMatch, AccessReliabilitySummary, and ProcessingSummary models in `src/wldm_url_filter/models.py`
- [X] T011 [P] Add unit tests for model validation rules in `tests/unit/test_models.py`
- [X] T012 Implement CSV input loading and column inference in `src/wldm_url_filter/ingestion.py`
- [X] T013 [P] Add unit tests for domain and keyword CSV ingestion in `tests/unit/test_ingestion.py`
- [X] T014 Implement URL normalization, duplicate detection, and unsafe-host rejection in `src/wldm_url_filter/config.py`
- [X] T015 [P] Add unit tests for URL safety constraints and SSRF-style rejection in `tests/unit/test_url_safety.py`
- [X] T016 Implement Simplified Chinese runtime diagnostic helpers in `src/wldm_url_filter/logging_config.py`
- [X] T017 [P] Add tests for Simplified Chinese runtime diagnostics and sensitive-value redaction in `tests/unit/test_logging_config.py`
- [X] T018 Implement shared output directory and run-id handling in `src/wldm_url_filter/outputs.py`
- [X] T019 [P] Add unit tests for output path creation and run-id handling in `tests/unit/test_outputs_base.py`
- [X] T020 Implement CLI argument parsing for `run`, `--domains`, `--keywords`, `--output-dir`, `--requester-accepted-failures`, `--run-id`, and `--min-recall-samples` in `src/wldm_url_filter/cli.py`
- [X] T021 [P] Add contract tests for the CLI argument schema in `tests/contract/test_cli_contract.py`

**Checkpoint**: Foundation complete; user stories can now be implemented and tested independently.

---

## Phase 3: User Story 1 - Discover Candidate Deep Pages (Priority: P1)

**Goal**: Expand valid root domains into specific candidate article, guide, review, or deep-content URLs.

**Independent Test**: With a relevant sample site and a junk site, candidate discovery emits deep URLs for the
relevant site, does not emit homepage-only matches when no relevant deep page exists, and expands from depth 2 to
depth 3 only when depth-2 recall is below the configured minimum sample count.

### Tests for User Story 1

- [X] T022 [P] [US1] Add unit tests for homepage link extraction, candidate URL normalization, and adaptive depth decisions in `tests/unit/test_discovery.py`
- [X] T023 [P] [US1] Add respx-backed integration tests for relevant, junk, redirecting, metadata-only, and depth-expansion domains in `tests/integration/test_discovery_flow.py`
- [X] T024 [P] [US1] Add CLI contract test for discovery-only dry-run output in `tests/contract/test_cli_discovery_contract.py`

### Implementation for User Story 1

- [X] T025 [US1] Implement homepage fetching and safe same-site link extraction in `src/wldm_url_filter/discovery.py`
- [X] T026 [US1] Implement sitemap and metadata candidate discovery fallbacks in `src/wldm_url_filter/discovery.py`
- [X] T027 [US1] Implement candidate prioritization by URL slug, title, primary heading, and core metadata plus adaptive depth behavior that starts at depth 2 and expands to depth 3 only when depth-2 recall is below the configured minimum sample count in `src/wldm_url_filter/discovery.py`
- [X] T028 [US1] Connect SourceDomain and TargetKeyword ingestion to candidate discovery orchestration in `src/wldm_url_filter/cli.py`
- [X] T029 [US1] Add Simplified Chinese diagnostics for discovery skips, redirects, and inaccessible homepages in `src/wldm_url_filter/discovery.py`
- [X] T030 [US1] Document discovery validation behavior in `specs/001-url-discovery-filter/quickstart.md`

**Checkpoint**: User Story 1 is independently testable with mocked sites and produces CandidatePage records.

---

## Phase 4: User Story 2 - Minimize Target URL Access Failures (Priority: P1)

**Goal**: Verify target URL reachability with a fast full-scope pass and timeout-only conservative retest.

**Independent Test**: With reachable, timeout-prone, invalid, and blocked URLs, the workflow retests timeout
failures and reports final success and failure rates by failure type.

### Tests for User Story 2

- [X] T031 [P] [US2] Add unit tests for reachability outcome and failure-type classification in `tests/unit/test_reachability.py`
- [X] T032 [P] [US2] Add respx-backed integration tests for fast pass success, timeout retest success, blocked access, redirect failure, and unsupported content in `tests/integration/test_reachability_flow.py`
- [X] T033 [P] [US2] Add contract tests for access reliability CSV columns and exit status behavior in `tests/contract/test_access_reliability_contract.py`

### Implementation for User Story 2

- [X] T034 [US2] Implement fast full-scope reachability pass with bounded concurrency in `src/wldm_url_filter/reachability.py`
- [X] T035 [US2] Implement timeout-only retest with lower or no concurrency and longer timeout allowance in `src/wldm_url_filter/reachability.py`
- [X] T036 [US2] Implement failure classification for timeout, connection failure, invalid URL, blocked access, redirect failure, and unsupported content in `src/wldm_url_filter/reachability.py`
- [X] T037 [US2] Implement final failure-rate calculation and optimization status decision in `src/wldm_url_filter/reachability.py`
- [X] T038 [US2] Implement access reliability CSV writing in `src/wldm_url_filter/outputs.py`
- [X] T039 [US2] Wire reachability checks and `--requester-accepted-failures` behavior into `src/wldm_url_filter/cli.py`
- [X] T040 [US2] Add Simplified Chinese diagnostics for access failures, timeout retests, and optimization-required status in `src/wldm_url_filter/reachability.py`
- [X] T075 [US2] Remove exact duplicate domain rows from `data/input_domains.csv`

**Checkpoint**: User Story 2 is independently testable with mocked URLs and produces the access reliability table.

---

## Phase 5: User Story 3 - Filter Pages by Keyword and Semantic Relevance (Priority: P1)

**Goal**: Retain only pages whose primary page signals clearly match exact keywords or close semantic variants.

**Independent Test**: With exact matches, close variants, utility pages, and off-topic pages, relevant pages are
retained with detected keyword evidence and irrelevant pages are discarded.

### Tests for User Story 3

- [ ] T041 [P] [US3] Add unit tests for exact keyword and close semantic variant matching in `tests/unit/test_relevance.py`
- [ ] T042 [P] [US3] Add unit tests for utility-page exclusion overriding incidental keyword evidence in `tests/unit/test_utility_exclusions.py`
- [ ] T043 [P] [US3] Add integration tests for candidate-to-accepted relevance decisions in `tests/integration/test_relevance_flow.py`

### Implementation for User Story 3

- [ ] T044 [US3] Implement primary signal extraction for URL slug, title, primary heading, and core metadata in `src/wldm_url_filter/relevance.py`
- [ ] T045 [US3] Implement exact keyword and rapidfuzz close-variant matching in `src/wldm_url_filter/relevance.py`
- [ ] T046 [US3] Implement utility-page exclusion patterns in `src/wldm_url_filter/relevance.py`
- [ ] T047 [US3] Implement RelevanceDecision scoring from 0 to 100 in `src/wldm_url_filter/relevance.py`
- [ ] T048 [US3] Preserve strongest RelevanceDecision for duplicate target URLs in `src/wldm_url_filter/relevance.py`
- [ ] T049 [US3] Wire relevance filtering after candidate discovery and reachability checks in `src/wldm_url_filter/cli.py`
- [ ] T050 [US3] Add Simplified Chinese diagnostics for rejected pages and matched keyword evidence in `src/wldm_url_filter/relevance.py`

**Checkpoint**: User Story 3 is independently testable with CandidatePage fixtures and produces AcceptedUrlMatch records.

---

## Phase 6: User Story 4 - Deliver a Clean Spreadsheet (Priority: P2)

**Goal**: Generate a clean accepted URL CSV with required columns and deduplicated final rows.

**Independent Test**: With accepted matches and duplicates, the output CSV contains only accepted records with the
required columns in order and no duplicate target URLs.

### Tests for User Story 4

- [ ] T051 [P] [US4] Add unit tests for accepted URL CSV ordering, required values, and duplicate removal in `tests/unit/test_accepted_url_output.py`
- [ ] T052 [P] [US4] Add contract tests for accepted URL output schema in `tests/contract/test_accepted_url_contract.py`
- [ ] T053 [P] [US4] Add end-to-end integration test for CLI generation of accepted URL output in `tests/integration/test_cli_output_flow.py`

### Implementation for User Story 4

- [ ] T054 [US4] Implement accepted URL CSV writing with Source Domain, Target URL, Detected Keyword, and Relevance Score in `src/wldm_url_filter/outputs.py`
- [ ] T055 [US4] Implement final accepted-row deduplication and strongest-evidence preservation in `src/wldm_url_filter/outputs.py`
- [ ] T056 [US4] Wire accepted URL output generation into CLI run flow in `src/wldm_url_filter/cli.py`
- [ ] T057 [US4] Add output success and empty-result Simplified Chinese diagnostics in `src/wldm_url_filter/outputs.py`
- [ ] T058 [US4] Update output validation guidance in `specs/001-url-discovery-filter/quickstart.md`

**Checkpoint**: User Story 4 produces the required accepted URL spreadsheet-compatible CSV.

---

## Phase 7: User Story 5 - Review Processing Coverage and Exclusions (Priority: P3)

**Goal**: Produce a processing summary that explains coverage, matches, exclusions, duplicates, and inaccessible domains.

**Independent Test**: With known relevant, irrelevant, duplicate, invalid, and inaccessible inputs, the summary
reports totals and separates inaccessible domains from accessed-but-irrelevant domains.

### Tests for User Story 5

- [ ] T059 [P] [US5] Add unit tests for ProcessingSummary count consistency in `tests/unit/test_processing_summary.py`
- [ ] T060 [P] [US5] Add integration tests for run-level summary generation across mixed input outcomes in `tests/integration/test_processing_summary_flow.py`
- [ ] T061 [P] [US5] Add contract tests for processing summary CSV columns and optimization status values in `tests/contract/test_processing_summary_contract.py`

### Implementation for User Story 5

- [ ] T062 [US5] Implement processing summary aggregation from ingestion, discovery, reachability, relevance, and output stages in `src/wldm_url_filter/outputs.py`
- [ ] T063 [US5] Implement processing summary CSV writing in `src/wldm_url_filter/outputs.py`
- [ ] T064 [US5] Wire summary generation into all CLI exit paths in `src/wldm_url_filter/cli.py`
- [ ] T065 [US5] Add Simplified Chinese diagnostics for run summary and optimization discussion points in `src/wldm_url_filter/cli.py`
- [ ] T066 [US5] Update processing summary validation guidance in `specs/001-url-discovery-filter/quickstart.md`

**Checkpoint**: User Story 5 produces a reviewer-ready processing summary for mixed input outcomes.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Validate the full feature against constitution, quickstart, security, quality, and delivery expectations.

- [ ] T067 [P] Run linting in the conda environment and fix issues in `src/wldm_url_filter/`
- [ ] T068 [P] Run type checking in the conda environment and fix issues in `src/wldm_url_filter/`
- [ ] T069 Run full pytest suite in the conda environment and fix failures in `tests/`
- [ ] T070 Run coverage gate greater than 80% in the conda environment and add tests in `tests/unit/` if needed
- [ ] T071 Validate quickstart commands and expected outputs using `specs/001-url-discovery-filter/quickstart.md`
- [ ] T072 Review generated project documentation and code comments for English-only project content in `specs/001-url-discovery-filter/` and `src/wldm_url_filter/`
- [ ] T073 Review runtime errors and logs for Simplified Chinese diagnostics and sensitive-value redaction in `src/wldm_url_filter/`
- [ ] T074 Re-check `.gitignore` after implementation to exclude new caches, logs, generated intermediates, local data outputs, and local environment files in `.gitignore`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; start here.
- **Foundational (Phase 2)**: Depends on Setup and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational; provides CandidatePage records.
- **User Story 2 (Phase 4)**: Depends on Foundational; can be built in parallel with US1 using URL fixtures.
- **User Story 3 (Phase 5)**: Depends on Foundational; can be built with CandidatePage fixtures, then integrated with US1 and US2.
- **User Story 4 (Phase 6)**: Depends on Foundational; can be built with AcceptedUrlMatch fixtures, then integrated with US3.
- **User Story 5 (Phase 7)**: Depends on Foundational; can be built with stage-result fixtures, then integrated with all stories.
- **Polish (Phase 8)**: Depends on all selected stories.

### User Story Dependencies

- **US1**: Independent after Foundational for candidate discovery.
- **US2**: Independent after Foundational for reachability, using target URL fixtures.
- **US3**: Independent after Foundational with candidate fixtures; full pipeline integration benefits from US1 and US2.
- **US4**: Independent after Foundational with accepted-match fixtures; final output depends on US3 for live pipeline value.
- **US5**: Independent after Foundational with summary fixtures; final summary depends on all stages for live pipeline value.

### Within Each User Story

- Write tests first and confirm they fail before implementation.
- Implement models or services before CLI wiring.
- Add Simplified Chinese runtime diagnostics in the same story phase as the behavior that emits them.
- Complete each story checkpoint before relying on it in later integration work.

### Parallel Opportunities

- T005, T006, T007, T008, and T009 can run in parallel after T002.
- T011, T013, T015, T017, T019, and T021 can run in parallel after T010 and their target skeleton files exist.
- Test tasks within each user story can run in parallel because they target different files.
- US1 and US2 can proceed in parallel after Foundational.
- US3, US4, and US5 can proceed in parallel using fixtures, then integrate after upstream stages are ready.
- Polish tasks T067 and T068 can run in parallel before full test and coverage gates.

---

## Parallel Example: User Story 1

```bash
# Start User Story 1 tests in parallel:
Task: "T022 Add unit tests for homepage link extraction and candidate URL normalization in tests/unit/test_discovery.py"
Task: "T023 Add respx-backed integration tests for relevant, junk, redirecting, and metadata-only domains in tests/integration/test_discovery_flow.py"
Task: "T024 Add CLI contract test for discovery-only dry-run output in tests/contract/test_cli_discovery_contract.py"
```

## Parallel Example: User Story 2

```bash
# Start User Story 2 tests in parallel:
Task: "T031 Add unit tests for reachability outcome and failure-type classification in tests/unit/test_reachability.py"
Task: "T032 Add respx-backed integration tests for fast pass success, timeout retest success, blocked access, redirect failure, and unsupported content in tests/integration/test_reachability_flow.py"
Task: "T033 Add contract tests for access reliability CSV columns and exit status behavior in tests/contract/test_access_reliability_contract.py"
```

## Parallel Example: User Story 3

```bash
# Start User Story 3 tests in parallel:
Task: "T041 Add unit tests for exact keyword and close semantic variant matching in tests/unit/test_relevance.py"
Task: "T042 Add unit tests for utility-page exclusion overriding incidental keyword evidence in tests/unit/test_utility_exclusions.py"
Task: "T043 Add integration tests for candidate-to-accepted relevance decisions in tests/integration/test_relevance_flow.py"
```

---

## Implementation Strategy

### MVP First (P1 Stories)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: US1 candidate discovery.
4. Complete Phase 4: US2 reachability minimization.
5. Complete Phase 5: US3 relevance filtering.
6. Stop and validate P1 stories independently before building final delivery polish.

### Incremental Delivery

1. Setup and Foundational phases establish the conda-restricted CLI and shared models.
2. US1 discovers candidate deep pages from noisy domains.
3. US2 verifies access reliability and optimization status.
4. US3 filters candidate pages into accepted matches.
5. US4 writes the accepted URL spreadsheet.
6. US5 writes the processing summary.
7. Polish validates quality, security, diagnostics, coverage, and quickstart behavior.

### Suggested MVP Scope

The MVP is the P1 story set: US1, US2, and US3. These stories prove the core challenge value: discover deep pages,
minimize access failures, and filter relevant URLs before delivery outputs are finalized.

## Notes

- All project commands must run inside `conda run -n wldm-url-filter` or after `conda activate wldm-url-filter`.
- Use English for documentation, task descriptions, comments, and commit messages.
- Runtime errors, warnings, and logs emitted by the application must be Simplified Chinese.
- Do not hardcode secrets, passwords, tokens, cookies, or other sensitive credentials.
- Generated intermediate files and local outputs must remain excluded from git.

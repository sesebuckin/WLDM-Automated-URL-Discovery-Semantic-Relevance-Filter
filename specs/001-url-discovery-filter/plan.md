# Implementation Plan: Automated URL Discovery and Semantic Relevance Filter

**Branch**: `N/A` | **Date**: 2026-06-16 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-url-discovery-filter/spec.md`

**Note**: Generated project documents MUST be written in English.

## Summary

Build a local Python CLI data pipeline that reads a noisy domain CSV and a target keyword CSV, discovers candidate
deep pages from each valid domain, verifies target URL reachability with a two-stage access process, filters pages
by exact keyword or close semantic-variant evidence in primary page signals, and exports clean spreadsheet-ready
deliverables. The required outputs are an accepted URL match CSV, an access reliability CSV, and a processing
summary that supports continued optimization when final access failures remain above 10%.

## Technical Context

**Language/Version**: Python 3.12 inside the dedicated conda environment `wldm-url-filter`

**Primary Dependencies**: Managed by `environment.yml`: `httpx`, `beautifulsoup4`, `pandas`, `pydantic`, `typer`,
`rapidfuzz`, `pytest`, `coverage`, `respx`, `pyyaml`, `ruff`, `mypy`

**Storage**: Local files only: CSV inputs, CSV outputs, optional JSON run metadata, and log files excluded from git

**Testing**: `pytest` with `coverage.py`; target unit test coverage greater than 80%

**Target Platform**: Local macOS/Linux CLI execution restricted to the dedicated Anaconda/conda environment

**Project Type**: CLI data pipeline

**Performance Goals**: Process approximately 3,000 root domains; use a fast full-scope first reachability pass;
retest 100% of first-pass timeout failures; produce final access failure rate <=10% or continue optimization until
the requester explicitly accepts remaining failures; start discovery at crawl depth 2 and expand an individual
domain or target URL scope to depth 3 only when depth-2 candidate recall is below the configured minimum recall
sample count N

**Constraints**: Run all project commands inside the dedicated conda environment `wldm-url-filter`; respect
per-domain politeness limits; cap crawl depth and candidate pages per domain; preserve precision by using adaptive
depth expansion instead of unconditional depth-3 crawling; never log sensitive values; emit runtime errors and logs
in Simplified Chinese; keep generated intermediate files out of git

**Scale/Scope**: Approximately 3,000 input domains, one keyword dataset, one accepted match CSV, one access
reliability CSV, one processing summary per run

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Python implementation**: PASS. The plan uses Python for production code, tests, scripts, and automation, all
  restricted to the dedicated conda environment `wldm-url-filter`.
- **English project content**: PASS. All generated project documents, planned comments, and commit-message guidance
  are English.
- **English identifiers**: PASS. Planned modules, functions, entities, and CLI fields use English identifiers.
- **Chinese runtime diagnostics**: PASS. Runtime errors and logs are explicitly required to be Simplified Chinese.
- **Clean Code and SOLID**: PASS. The design separates ingestion, crawling, reachability, relevance, output, and
  reporting services.
- **Unit test coverage**: PASS. The testing plan requires `pytest` and coverage greater than 80%.
- **Security by default**: PASS. The plan includes input validation, SSRF-style URL constraints, secret handling, and
  sensitive-log prevention.
- **Ignore-rule hygiene**: PASS. `.gitignore` exists and excludes caches, logs, local environments, generated
  intermediates, and local agent config. The tracked `environment.yml` is the canonical environment definition.

## Project Structure

### Documentation (this feature)

```text
specs/001-url-discovery-filter/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── cli.md
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
src/
├── wldm_url_filter/
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   ├── models.py
│   ├── ingestion.py
│   ├── discovery.py
│   ├── reachability.py
│   ├── relevance.py
│   ├── outputs.py
│   └── logging_config.py
└── scripts/
    └── run_sample.py

tests/
├── contract/
├── integration/
└── unit/

data/
├── input/
└── output/

environment.yml
```

**Structure Decision**: Use a single Python CLI project because the feature is a batch-processing deliverable with
local spreadsheet inputs and outputs. A web service would add unnecessary operational surface area.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Post-Design Constitution Check

- **Python implementation**: PASS. Design artifacts define a Python CLI/data-pipeline structure restricted to the
  dedicated conda environment `wldm-url-filter`.
- **English project content**: PASS. `plan.md`, `research.md`, `data-model.md`, `contracts/cli.md`, and
  `quickstart.md` are English.
- **English identifiers**: PASS. Data entities, fields, and contract names use English identifiers.
- **Chinese runtime diagnostics**: PASS. CLI contract and quickstart require Simplified Chinese runtime errors/logs.
- **Clean Code and SOLID**: PASS. The data model and contracts support separate services with focused
  responsibilities.
- **Unit test coverage**: PASS. Quickstart and future tasks include coverage verification greater than 80%.
- **Security by default**: PASS. Research and contracts include input validation, URL safety constraints, and
  sensitive-log prevention.
- **Ignore-rule hygiene**: PASS. `.gitignore` covers planned caches, logs, environments, and intermediate outputs;
  `environment.yml` remains tracked as the reproducible conda environment contract.

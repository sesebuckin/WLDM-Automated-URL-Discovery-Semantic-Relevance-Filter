# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]

**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. Generated project documents MUST be written
in English.

## Summary

[Extract from feature spec: primary requirement, user value, and technical approach]

## Technical Context

<!--
  ACTION REQUIRED: Replace this section with real technical details. Mark unclear items as NEEDS CLARIFICATION.
-->

**Language/Version**: Python [version, e.g., 3.11; or NEEDS CLARIFICATION]

**Primary Dependencies**: [e.g., requests, BeautifulSoup, sentence-transformers, FastAPI; or NEEDS CLARIFICATION]

**Storage**: [if applicable, e.g., files, SQLite, PostgreSQL; otherwise N/A]

**Testing**: [e.g., pytest, coverage.py; or NEEDS CLARIFICATION]

**Target Platform**: [e.g., macOS/Linux, local CLI, web service; or NEEDS CLARIFICATION]

**Project Type**: [e.g., library/cli/web-service/data-pipeline; or NEEDS CLARIFICATION]

**Performance Goals**: [domain-specific metrics, e.g., URLs processed per minute, relevance scoring latency; or NEEDS CLARIFICATION]

**Constraints**: [domain-specific constraints, e.g., crawl rate, memory limit, offline capability; or NEEDS CLARIFICATION]

**Scale/Scope**: [domain-specific scale, e.g., number of URLs, data sources, concurrent jobs; or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Python implementation**: Does the plan use Python for production code, tests, scripts, and automation by default?
- **English project content**: Are documents, code comments, and commit-message guidance written in English?
- **English identifiers**: Are variable names, function names, class names, module names, and public APIs clear English?
- **Chinese runtime diagnostics**: Are emitted runtime error messages and log messages specified as Simplified Chinese?
- **Clean Code and SOLID**: Does the design explain module boundaries, responsibilities, complexity control, and justified abstractions?
- **Unit test coverage**: Does the plan include automated tests and a unit test coverage target greater than 80%?
- **Security by default**: Does the plan cover OWASP Top 10, input validation, secret handling, and sensitive-log prevention?
- **Ignore-rule hygiene**: Does the plan check `.gitignore` for caches, logs, build artifacts, local environments, and local agent config?

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit-plan output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks output)
```

### Source Code (repository root)

<!--
  ACTION REQUIRED: Delete unused options and expand the selected structure with real paths.
  The delivered plan must not keep "Option" labels.
-->

```text
# [REMOVE IF UNUSED] Single Python project (default)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Python web service
src/
├── models/
├── services/
├── api/
└── security/

tests/
├── contract/
├── integration/
└── unit/
```

**Structure Decision**: [Document the selected structure and reference the real directories above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., additional abstraction] | [current need] | [why the simpler approach is insufficient] |

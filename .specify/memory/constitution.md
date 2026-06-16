<!--
Sync Impact Report
Version change: 1.0.0 -> 2.0.0
Modified principles:
- Previous principle I (Python implementation language) -> I. Python Implementation Language
- Previous principle II (Simplified Chinese delivery language) -> II. English Project Content and Chinese Runtime Diagnostics
- Previous principle III (Clean Code and SOLID) -> III. Clean Code and SOLID
- Previous principle IV (test coverage and verifiability) -> IV. Unit Test Coverage and Verifiability
- Previous principle V (security by default) -> V. Security by Default
Added sections:
- Technical and Delivery Constraints
- Development Workflow and Quality Gates
Removed sections:
- None
Templates requiring updates:
- ✅ .specify/templates/plan-template.md
- ✅ .specify/templates/spec-template.md
- ✅ .specify/templates/tasks-template.md
- ✅ .specify/templates/commands/*.md (directory not present)
Runtime guidance docs:
- ✅ AGENTS.md
Follow-up TODOs:
- None
-->
# WLDM Automated URL Discovery and Semantic Relevance Filter Constitution

## Core Principles

### I. Python Implementation Language
Production code, tests, data-processing scripts, command-line tooling, and automation MUST use Python by
default. A non-Python file is allowed only when required by configuration formats, packaging metadata, or
external tooling that cannot be expressed in Python.

Rationale: A single implementation language keeps URL discovery, semantic filtering, testing, and operational
automation easier to maintain and review.

### II. English Project Content and Chinese Runtime Diagnostics
All project documentation, code comments, and commit messages MUST be written in English. Code variable names,
function names, class names, module names, and public API names MUST also use clear English identifiers.
Runtime error messages and log messages that are emitted by the application and are not project documentation
MUST use Simplified Chinese.

Rationale: English project content preserves consistency with the Python ecosystem and external tooling, while
Chinese runtime diagnostics keep operational feedback readable for the intended users.

### III. Clean Code and SOLID
Production code MUST follow Clean Code principles: clear naming, focused functions, low duplication, explicit
module boundaries, and controlled complexity. Object-oriented or replaceable components MUST follow SOLID,
especially single responsibility, dependency inversion, and interface segregation. New abstractions MUST have a
specific reason: reducing complexity, isolating change, or enabling meaningful reuse.

Rationale: The project combines discovery, filtering, scoring, and output workflows. Clear boundaries make the
system easier to change without introducing regressions.

### IV. Unit Test Coverage and Verifiability
Unit test coverage MUST remain greater than 80%. New features MUST include automated tests, and bug fixes MUST
include a test that reproduces the issue before the fix. Core URL discovery, semantic relevance decisions,
deduplication, error handling, and security boundaries MUST be covered by unit tests or integration tests.

Rationale: Measurable coverage and reproducible tests reduce regressions in ranking, filtering, and network
handling behavior.

### V. Security by Default
The project MUST follow OWASP Top 10 security standards. Source code MUST NOT hardcode secrets, passwords,
tokens, cookies, or other sensitive credentials. Sensitive configuration MUST be injected through environment
variables, secret management, or untracked local configuration. All external input, URLs, file paths, and network
responses MUST be validated, constrained, and handled safely. Logs MUST NOT expose sensitive information.

Rationale: Automated URL discovery touches untrusted inputs and network content, so secure defaults reduce
injection, leakage, unsafe requests, and supply-chain risk.

## Technical and Delivery Constraints

- Python version, dependency management, testing framework, and runtime commands MUST be documented in each
  feature plan.
- The default project layout SHOULD use `src/` for implementation code and `tests/` for tests, organized by
  `unit/`, `integration/`, and `contract/` where applicable.
- The project MUST maintain a default `.gitignore` and keep it synchronized during development. It MUST exclude
  temporary files, caches, logs, build artifacts, coverage artifacts, local environment files, non-final generated
  outputs, and local agent configuration.
- Runtime error and log behavior MUST be validated where a feature introduces user-visible failures or operational
  diagnostics, and those emitted messages MUST be Simplified Chinese.
- Every new external dependency MUST document its purpose, maintenance status, and security impact. Unused
  dependencies MUST be removed.

## Development Workflow and Quality Gates

- Every feature plan MUST pass the constitution check before research begins and MUST be checked again after
  design is complete.
- Every specification MUST include independently verifiable user scenarios, edge cases, security-related
  requirements, and measurable success criteria.
- Every task list MUST include testing, implementation, English project-content checks, Chinese runtime-diagnostic
  checks, security checks, and `.gitignore` synchronization checks.
- Before merge, automated tests MUST run and unit test coverage MUST be greater than 80%. If tests cannot run,
  the delivery notes MUST record the reason and risk.
- Code review MUST verify Python implementation, English documentation and comments, English commit-message
  readiness, English identifiers, Clean Code, SOLID, unit test coverage, OWASP Top 10 alignment, secret handling,
  sensitive-log prevention, and ignore-rule hygiene.

## Governance

This constitution supersedes all other project practices, templates, and temporary conventions. Every feature
plan, specification, task list, code review, and release activity MUST comply with this constitution.

Constitution amendments MUST be submitted as documentation changes and MUST explain the reason, impact, version
change, and any templates or runtime guidance files that need synchronization. Versioning follows semantic
versioning:

- MAJOR: Removes, redefines, or relaxes an existing core principle in a backward-incompatible way.
- MINOR: Adds a core principle, mandatory section, or materially expands governance requirements.
- PATCH: Clarifies wording, fixes typos, or adds non-semantic explanation.

Each amendment MUST update the Sync Impact Report, version, and last amended date. Plan, specification, task
templates, and runtime guidance documents MUST remain aligned with the constitution. When conflicts are found,
this constitution is authoritative and the conflicting artifact MUST be corrected.

**Version**: 2.0.0 | **Ratified**: 2026-06-16 | **Last Amended**: 2026-06-16

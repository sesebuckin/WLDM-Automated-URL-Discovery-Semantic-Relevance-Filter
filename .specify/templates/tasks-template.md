---

description: "Task list template for feature implementation"
---

# Tasks: [FEATURE NAME]

**Input**: Design documents from `/specs/[###-feature-name]/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The project constitution requires automated tests for new features and unit test coverage greater
than 80%.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions
- Task descriptions, documentation, comments, and commit-message guidance must be written in English

## Path Conventions

- **Single Python project**: `src/`, `tests/` at repository root
- **Python web service**: `src/api/`, `src/services/`, `tests/`
- Paths must be adjusted based on the structure decision in plan.md

<!--
  ============================================================================
  IMPORTANT: The tasks below are sample tasks. /speckit-tasks MUST replace them
  with real tasks based on the specification and plan.

  Generated tasks MUST cover:
  - User stories and priorities
  - Functional requirements, entities, and contracts
  - Python implementation
  - English project content
  - Simplified Chinese runtime diagnostics
  - Test coverage, security checks, and .gitignore synchronization
  - Clean Code, SOLID, and OWASP Top 10 requirements

  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize project structure, tooling, and quality gates

- [ ] T001 Create the Python project structure from the implementation plan
- [ ] T002 Initialize Python dependency management and runtime entry points
- [ ] T003 [P] Configure linting, formatting, and type-checking tools
- [ ] T004 [P] Configure pytest and coverage reporting with a greater-than-80% coverage gate
- [ ] T005 [P] Create or update `.gitignore` for caches, logs, build artifacts, local environments, and local agent config

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Complete shared foundations that must exist before user-story work begins

**Critical Requirement**: No user story implementation can begin until this phase is complete

Example foundational tasks (adjust based on the project):

- [ ] T006 Create configuration loading that prevents hardcoded secrets, passwords, tokens, or cookies
- [ ] T007 [P] Implement input validation and URL safety constraints
- [ ] T008 [P] Implement Simplified Chinese runtime error handling and logging infrastructure
- [ ] T009 Create core models or entities
- [ ] T010 Add security boundary checks for relevant OWASP Top 10 risks
- [ ] T011 Review module responsibilities for Clean Code and SOLID alignment

**Checkpoint**: Foundation complete; user stories can now be implemented in parallel

---

## Phase 3: User Story 1 - [Title] (Priority: P1)

**Goal**: [Brief description of the value this story delivers]

**Independent Test**: [How to verify this story independently]

### Tests for User Story 1

> **Note: Write these tests first and confirm they fail before implementation**

- [ ] T012 [P] [US1] Write contract test for [contract/interface] in tests/contract/test_[name].py
- [ ] T013 [P] [US1] Write integration test for [user journey] in tests/integration/test_[name].py
- [ ] T014 [P] [US1] Write unit test for core logic in tests/unit/test_[name].py

### Implementation for User Story 1

- [ ] T015 [P] [US1] Create [Entity1] model in src/models/[entity1].py
- [ ] T016 [P] [US1] Create [Entity2] model in src/models/[entity2].py
- [ ] T017 [US1] Implement [Service] in src/services/[service].py (depends on T015, T016)
- [ ] T018 [US1] Implement [entry point/feature] in src/[location]/[file].py
- [ ] T019 [US1] Add Simplified Chinese runtime errors, Simplified Chinese logs, and input validation
- [ ] T020 [US1] Verify no sensitive data is written to code, logs, or test fixtures

**Checkpoint**: User Story 1 should be independently runnable, testable, and demonstrable

---

## Phase 4: User Story 2 - [Title] (Priority: P2)

**Goal**: [Brief description of the value this story delivers]

**Independent Test**: [How to verify this story independently]

### Tests for User Story 2

- [ ] T021 [P] [US2] Write contract test in tests/contract/test_[name].py
- [ ] T022 [P] [US2] Write integration test in tests/integration/test_[name].py
- [ ] T023 [P] [US2] Write unit test in tests/unit/test_[name].py

### Implementation for User Story 2

- [ ] T024 [P] [US2] Create [Entity] model in src/models/[entity].py
- [ ] T025 [US2] Implement [Service] in src/services/[service].py
- [ ] T026 [US2] Implement [entry point/feature] in src/[location]/[file].py
- [ ] T027 [US2] Integrate with User Story 1 components if needed
- [ ] T028 [US2] Add Simplified Chinese runtime errors, Simplified Chinese logs, and security validation

**Checkpoint**: User Stories 1 and 2 should both be independently runnable, testable, and demonstrable

---

## Phase 5: User Story 3 - [Title] (Priority: P3)

**Goal**: [Brief description of the value this story delivers]

**Independent Test**: [How to verify this story independently]

### Tests for User Story 3

- [ ] T029 [P] [US3] Write contract test in tests/contract/test_[name].py
- [ ] T030 [P] [US3] Write integration test in tests/integration/test_[name].py
- [ ] T031 [P] [US3] Write unit test in tests/unit/test_[name].py

### Implementation for User Story 3

- [ ] T032 [P] [US3] Create [Entity] model in src/models/[entity].py
- [ ] T033 [US3] Implement [Service] in src/services/[service].py
- [ ] T034 [US3] Implement [entry point/feature] in src/[location]/[file].py
- [ ] T035 [US3] Add Simplified Chinese runtime errors, Simplified Chinese logs, and security validation

**Checkpoint**: All target user stories should be independently runnable, testable, and demonstrable

---

[Add more user-story phases as needed while keeping the same structure]

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Address quality, security, and delivery concerns that affect multiple user stories

- [ ] TXXX [P] Update English documentation in docs/
- [ ] TXXX Clean up code and remove duplication; verify Clean Code and SOLID boundaries
- [ ] TXXX [P] Add unit tests and confirm coverage remains greater than 80%
- [ ] TXXX Run OWASP Top 10 security checks
- [ ] TXXX Verify documentation, comments, task descriptions, and commit-message guidance are English
- [ ] TXXX Verify runtime error messages and log messages emitted by the application are Simplified Chinese
- [ ] TXXX Run quickstart.md validation
- [ ] TXXX Re-check `.gitignore` for newly introduced temporary outputs and local configuration

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories
- **User Stories (Phase 3+)**: Depend on Foundational completion
  - Can proceed in parallel if team capacity allows
  - Can also proceed sequentially in priority order (P1 → P2 → P3)
- **Polish phase**: Depends on all target user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational and has no dependency on other stories
- **User Story 2 (P2)**: Can start after Foundational; may integrate with US1 but must remain independently testable
- **User Story 3 (P3)**: Can start after Foundational; may integrate with US1/US2 but must remain independently testable

### Within Each User Story

- Write tests first and confirm they fail before implementation
- Build models before services, then entry points or interfaces
- Build core logic before integration
- Complete each story before moving to the next priority or polish phase

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel within Phase 2
- Different user stories can be handled in parallel after Foundational completion
- Different test files and model files within one story can run in parallel

---

## Parallel Example: User Story 1

```bash
# Start User Story 1 test tasks in parallel:
Task: "Write contract test for [contract/interface] in tests/contract/test_[name].py"
Task: "Write integration test for [user journey] in tests/integration/test_[name].py"
Task: "Write unit test for core logic in tests/unit/test_[name].py"

# Create User Story 1 models in parallel:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Stop and validate User Story 1 independently
5. Demonstrate or deliver when ready

### Incremental Delivery

1. Complete Setup and Foundational phases
2. Add User Story 1, test independently, and demonstrate
3. Add User Story 2, test independently, and demonstrate
4. Add User Story 3, test independently, and demonstrate
5. Each story must add value without breaking previous stories

### Parallel Team Strategy

1. Team completes Setup and Foundational phases together
2. After Foundational completion:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] means different files and no dependency, so the task can run in parallel
- [Story] labels map tasks to user stories for traceability
- Each user story must be independently completable and testable
- Confirm relevant tests fail before implementation
- Use English commit messages after each task or logical task group
- Avoid vague tasks, same-file conflicts, and cross-story dependencies that break independence

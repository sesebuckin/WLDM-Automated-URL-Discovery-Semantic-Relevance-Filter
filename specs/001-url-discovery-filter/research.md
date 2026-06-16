# Research: Automated URL Discovery and Semantic Relevance Filter

## Decision: Use a local Python CLI data pipeline

**Rationale**: The deliverable is a batch workflow over CSV inputs with CSV outputs. A local CLI is easy to run,
test, package, and explain in a challenge submission. It also keeps secrets and data local.

**Alternatives considered**:
- Notebook-only workflow: easier for exploration but weaker for repeatable validation and automated tests.
- Web service: unnecessary for a one-run spreadsheet deliverable and increases operational complexity.

## Decision: Require a dedicated conda environment

**Rationale**: Project execution must be isolated inside Anaconda/conda to keep runtime dependencies reproducible
and separate from the user's base environment. `environment.yml` is the canonical dependency contract, and all run,
test, lint, and validation commands should use `conda activate wldm-url-filter` or `conda run -n wldm-url-filter`.

**Alternatives considered**:
- Python `venv`: simple but does not satisfy the project requirement to restrict execution to Anaconda/conda.
- Base conda environment: convenient but risks dependency drift and conflicts with unrelated projects.
- Ad hoc `pip install` commands: less reproducible and harder to validate across machines.

## Decision: Use two-stage reachability detection

**Rationale**: The specification requires a fast full-scope pass followed by timeout-only retesting with lower or no
concurrency and longer timeout allowance. This separates obvious failures from timeout-sensitive sites and directly
supports the <=10% failure-rate goal.

**Alternatives considered**:
- Single fast pass: faster, but would overcount timeout failures.
- Single slow pass: maximizes patience but wastes time on clearly reachable or invalid targets.

## Decision: Treat access reliability as a first-class output

**Rationale**: The feature requires an additional table with success count, success rate, failure count, failure
rate, failure type, and failure type count. Modeling this output separately makes validation and optimization loops
testable.

**Alternatives considered**:
- Embed reliability columns in the accepted match CSV: mixes accepted content with failed access attempts.
- Only write logs: harder for reviewers to inspect and compare.

## Decision: Use primary page signals for relevance

**Rationale**: The clarified rule accepts exact keywords or close semantic variants when at least one primary page
signal clearly matches. Primary signals are URL slug, title, primary heading, and core metadata. This keeps the
filter precise while avoiding missed pages that have one strong signal.

**Alternatives considered**:
- Exact keyword only: high precision but poor recall for close variants.
- Two-signal minimum: safer but likely misses relevant articles with sparse metadata.
- Broad semantic match followed by manual review: too noisy for the precision goal.

## Decision: Use adaptive crawl depth for candidate discovery

**Rationale**: Each domain or target URL discovery scope starts at depth 2 to protect precision and avoid pulling
large numbers of archive, tag, pagination, utility, and navigation pages into the candidate pool. If the depth-2
search returns fewer than the configured minimum recall sample count N, that individual scope expands to depth 3.
Scopes that already meet N at depth 2 do not expand. This makes recall recovery selective instead of turning every
domain into a deeper crawl.

**Alternatives considered**:
- Always crawl depth 3: improves recall but increases noise, runtime, and the chance of irrelevant junk-domain
  candidates.
- Fixed depth 2 only: best for precision and speed, but may miss relevant content on sites with one extra listing
  layer.
- Unlimited or open-ended crawling: incompatible with the approximately 3,000-domain scale and precision-first
  success metric.

## Decision: Use lightweight lexical semantic matching first

**Rationale**: `rapidfuzz` supports close lexical variants and typo-tolerant matching without requiring large local
models. This is a practical baseline for URL slug, title, heading, and metadata. The design can add embedding-based
matching later if precision review shows gaps.

**Alternatives considered**:
- Heavy embedding model by default: stronger semantics but increases runtime, installation size, and reproducibility
  risk for a challenge submission.
- Exact string matching only: simpler but fails the close-semantic-variant requirement.

## Decision: Use file-based outputs and no database

**Rationale**: The requested deliverables are spreadsheet-compatible files. CSV plus optional JSON run metadata is
sufficient for the expected scale of approximately 3,000 domains.

**Alternatives considered**:
- SQLite: useful for very large crawl histories but unnecessary for the requested sample-data deliverable.
- External database: adds setup burden and security surface without clear benefit.

## Decision: Apply URL safety constraints before network access

**Rationale**: Automated URL discovery touches untrusted domains. Inputs must be normalized and constrained before
access to reduce SSRF-style risks, invalid requests, and noisy failures.

**Alternatives considered**:
- Trust input domains: simpler but unsafe with messy real-world data.
- Manual pre-cleaning only: not repeatable and weakens automated validation.

## Decision: Use `respx` for HTTP behavior tests

**Rationale**: Reachability and crawling behavior must be tested without depending on live external sites. `respx`
can mock `httpx` requests and simulate timeouts, redirects, blocked access, and successful responses.

**Alternatives considered**:
- Live-site integration tests only: flaky and hard to reproduce.
- Handwritten fake network layer only: useful for unit tests, but weaker for contract-like HTTP behavior.

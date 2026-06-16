# Quickstart: Automated URL Discovery and Semantic Relevance Filter

## Prerequisites

- Anaconda or Miniconda with `conda` available on `PATH`
- Dedicated conda environment defined by `environment.yml`
- Input files available at:
  - `data/input/Input_Domains.csv`
  - `data/input/Target_Keywords.csv`
- Local environment variables or configuration files must not contain secrets committed to git.

## Setup

```bash
conda env create -f environment.yml
conda activate wldm-url-filter
python -m pip install -e .
```

If the environment already exists, update it instead:

```bash
conda env update -f environment.yml --prune
conda activate wldm-url-filter
```

## Run the Pipeline

```bash
conda run -n wldm-url-filter wldm-url-filter run \
  --domains data/input/Input_Domains.csv \
  --keywords data/input/Target_Keywords.csv \
  --output-dir data/output
```

Expected deliverables:

- `data/output/<run-id>_accepted_urls.csv`
- `data/output/<run-id>_access_reliability.csv`
- `data/output/<run-id>_processing_summary.csv`

## Validate Adaptive Discovery Depth

Run the pipeline with the default precision-first crawl settings. Each domain or target URL discovery scope starts
at depth 2. If the depth-2 pass returns fewer than the configured minimum recall sample count N, only that scope
expands to depth 3. Scopes that already meet N at depth 2 must not expand.

For a discovery-only dry run, write the candidate-page CSV before reachability and relevance stages:

```bash
conda run -n wldm-url-filter wldm-url-filter run \
  --domains data/input/Input_Domains.csv \
  --keywords data/input/Target_Keywords.csv \
  --output-dir data/output \
  --run-id sample-discovery \
  --discovery-only
```

Expected discovery dry-run deliverable:

- `data/output/sample-discovery_candidate_pages.csv`

When validating a representative sample, verify:

- Relevant sites with enough depth-2 candidates do not perform unnecessary depth-3 crawling.
- Sites with fewer than N depth-2 candidates are retried at depth 3 before final candidate selection.
- Depth expansion does not bypass utility-page exclusions or relevance filtering.
- The candidate dry-run CSV contains deep candidate URLs, not homepage-only placeholders.
- Redirects are logged in Simplified Chinese and only same-site final URLs are retained.
- Sitemap and metadata fallbacks can contribute candidate URLs when homepage links are sparse.

## Validate Accepted URL Output

Open `<run-id>_accepted_urls.csv` and verify:

- Columns appear in this order: Source Domain, Target URL, Detected Keyword, Relevance Score.
- Rows contain accepted URLs only.
- Duplicate target URLs do not appear more than once, and duplicate equivalents keep the strongest relevance
  evidence.
- At least 90% of accepted rows in a manual sample are relevant to a target keyword or close semantic variant.
- At least 90% of accepted rows in a manual sample are deep URLs rather than only source homepages.

## Validate Access Reliability Output

Open `<run-id>_access_reliability.csv` and verify:

- Columns appear in this order: Success Count, Success Rate, Failure Count, Failure Rate, Failure Type,
  Failure Type Count.
- 100% of first-pass timeout failures were retested or reported with a reason why retesting was not possible.
- Final failure rate is <=10%, or the processing summary marks the run as not ready for delivery.

If final failure rate is greater than 10%, continue optimization and rerun the pipeline until:

- final failure rate is <=10%, or
- the requester explicitly accepts the documented remaining failures and the run is executed with
  `--requester-accepted-failures`.

## Validate Processing Summary

Open `<run-id>_processing_summary.csv` and verify:

- Valid, duplicate, invalid, inaccessible, matched, and excluded counts are present.
- Domains that could not be accessed are distinct from domains that were accessed but found irrelevant.
- `optimization_status` is one of `ready`, `optimize_again`, or `accepted_by_requester`.

## Run Tests

```bash
conda run -n wldm-url-filter pytest
conda run -n wldm-url-filter coverage run -m pytest
conda run -n wldm-url-filter coverage report --fail-under=80
```

Expected outcome:

- All tests pass.
- Unit test coverage is greater than 80%.
- Runtime error and log message tests assert Simplified Chinese diagnostics.

## Contract Reference

See [contracts/cli.md](./contracts/cli.md) for the command, input, output, and exit-behavior contract.

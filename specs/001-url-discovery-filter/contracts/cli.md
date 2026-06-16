# CLI Contract: Automated URL Discovery and Semantic Relevance Filter

## Command

```bash
conda run -n wldm-url-filter wldm-url-filter run \
  --domains data/input/Input_Domains.csv \
  --keywords data/input/Target_Keywords.csv \
  --output-dir data/output
```

All project commands MUST run inside the dedicated conda environment `wldm-url-filter`.

## Required Inputs

### `--domains`

Spreadsheet-compatible CSV containing root-domain records.

**Accepted shape**:
- A header named `domain`, `source_domain`, or an equivalent first column containing domain values.
- Blank rows, malformed domains, duplicates, mixed protocol values, and trailing paths are accepted as input noise
  and handled during validation.

### `--keywords`

Spreadsheet-compatible CSV containing target niche keywords.

**Accepted shape**:
- A header named `keyword`, `target_keyword`, or an equivalent first column containing keyword values.
- Blank and duplicate keywords are ignored after normalization.

### `--output-dir`

Directory where final deliverables and run metadata are written.

## Optional Inputs

### `--requester-accepted-failures`

Boolean flag that records requester acceptance of documented remaining access failures when final failure rate is
greater than 10%.

Default: `false`

### `--run-id`

Short run identifier used in output filenames.

Default: generated timestamp.

### `--min-recall-samples`

Minimum candidate sample count N required after depth-2 discovery before skipping depth expansion for an individual
domain or target URL scope.

Default: implementation configuration value.

## Outputs

### Accepted URL Matches

File: `<output-dir>/<run-id>_accepted_urls.csv`

Required columns, in order:

| Column | Description |
|--------|-------------|
| Source Domain | Normalized source domain that led to the accepted page |
| Target URL | Accepted deep URL or qualifying homepage URL |
| Detected Keyword | Keyword that triggered the strongest match |
| Relevance Score | Confidence score from 0 to 100 |

### Access Reliability Table

File: `<output-dir>/<run-id>_access_reliability.csv`

Required columns, in order:

| Column | Description |
|--------|-------------|
| Success Count | Final successful target URL access attempts |
| Success Rate | Final success percentage after timeout retesting |
| Failure Count | Final failed target URL access attempts |
| Failure Rate | Final failure percentage after timeout retesting |
| Failure Type | Failure category |
| Failure Type Count | Count for the failure category |

### Processing Summary

File: `<output-dir>/<run-id>_processing_summary.csv`

Required columns:
- `total_input_rows`
- `valid_domains`
- `invalid_domains`
- `duplicate_domains`
- `domains_attempted`
- `domains_with_matches`
- `accepted_url_count`
- `excluded_candidate_count`
- `inaccessible_domain_count`
- `optimization_status`

## Exit Behavior

| Condition | Exit Status | Required Behavior |
|-----------|-------------|-------------------|
| Completed and final access failure rate <=10% | `0` | Write all outputs and mark summary as `ready` |
| Completed, failure rate >10%, requester accepted failures | `0` | Write all outputs and mark summary as `accepted_by_requester` |
| Completed, failure rate >10%, requester did not accept failures | `2` | Write outputs, mark summary as `optimize_again`, and emit Simplified Chinese diagnostics |
| Invalid input files | `1` | Emit Simplified Chinese diagnostics and do not write final accepted output |
| Invalid adaptive-depth settings | `1` | Emit Simplified Chinese diagnostics and do not start network access |
| Unexpected runtime failure | `1` | Emit Simplified Chinese diagnostics without exposing sensitive data |

## Runtime Diagnostic Language

All runtime errors, warnings, and logs emitted by the application MUST be Simplified Chinese. Project documents,
comments, commit messages, identifiers, and this contract remain English.

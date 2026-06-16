"""Shared output path and run identifier handling."""

from __future__ import annotations

import csv
import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from wldm_url_filter.config import UnsafeUrlError, normalized_url_key
from wldm_url_filter.logging_config import log_runtime_diagnostic
from wldm_url_filter.models import AcceptedUrlMatch, AccessReliabilitySummary, CandidatePage

LOGGER = logging.getLogger(__name__)
_RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
ACCEPTED_URL_FIELDNAMES = [
    "Source Domain",
    "Target URL",
    "Detected Keyword",
    "Relevance Score",
]


@dataclass(frozen=True, slots=True)
class RunOutputPaths:
    """Resolved output file paths for one pipeline run."""

    output_dir: Path
    run_id: str
    accepted_urls: Path
    access_reliability: Path
    processing_summary: Path
    candidate_pages: Path


def generate_run_id(now: datetime | None = None) -> str:
    """Generate a stable, filename-safe run identifier."""
    timestamp = now or datetime.now(UTC)
    return timestamp.strftime("%Y%m%d-%H%M%S")


def validate_run_id(run_id: str) -> str:
    """Validate a run identifier before it is used in filenames."""
    clean_run_id = run_id.strip()
    if not _RUN_ID_PATTERN.fullmatch(clean_run_id):
        raise ValueError("run_id must contain only letters, numbers, underscores, and hyphens")
    return clean_run_id


def prepare_output_directory(output_dir: Path) -> Path:
    """Create and return the output directory."""
    resolved = output_dir.expanduser()
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def resolve_run_output_paths(output_dir: Path, run_id: str | None = None) -> RunOutputPaths:
    """Resolve all Phase 2 output paths for a pipeline run."""
    prepared_dir = prepare_output_directory(output_dir)
    clean_run_id = validate_run_id(run_id or generate_run_id())
    return RunOutputPaths(
        output_dir=prepared_dir,
        run_id=clean_run_id,
        accepted_urls=prepared_dir / f"{clean_run_id}_accepted_urls.csv",
        access_reliability=prepared_dir / f"{clean_run_id}_access_reliability.csv",
        processing_summary=prepared_dir / f"{clean_run_id}_processing_summary.csv",
        candidate_pages=prepared_dir / f"{clean_run_id}_candidate_pages.csv",
    )


def write_candidate_pages_csv(path: Path, candidates: list[CandidatePage]) -> None:
    """Write discovery-only candidate pages to a spreadsheet-compatible CSV."""
    fieldnames = [
        "Source Domain",
        "Target URL",
        "Discovery Source",
        "URL Slug",
        "Title",
        "Primary Heading",
        "Core Metadata",
        "Utility Page Flag",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for candidate in candidates:
            writer.writerow(
                {
                    "Source Domain": candidate.source_domain,
                    "Target URL": candidate.target_url,
                    "Discovery Source": candidate.discovery_source.value,
                    "URL Slug": candidate.url_slug,
                    "Title": candidate.title,
                    "Primary Heading": candidate.primary_heading,
                    "Core Metadata": candidate.core_metadata,
                    "Utility Page Flag": candidate.utility_page_flag,
                }
            )


def deduplicate_accepted_url_matches(
    matches: list[AcceptedUrlMatch],
) -> list[AcceptedUrlMatch]:
    """Remove duplicate accepted target URLs while preserving strongest evidence."""
    strongest_by_key: dict[str, AcceptedUrlMatch] = {}
    ordered_keys: list[str] = []
    for match in matches:
        try:
            key = normalized_url_key(match.target_url, allowed_domain=match.source_domain)
        except UnsafeUrlError:
            key = match.target_url

        current = strongest_by_key.get(key)
        if current is None:
            ordered_keys.append(key)
            strongest_by_key[key] = match
            continue
        if match.relevance_score > current.relevance_score:
            strongest_by_key[key] = match

    return [strongest_by_key[key] for key in ordered_keys]


def accepted_output_diagnostic(path: Path, row_count: int) -> str:
    """Log and return the accepted URL output diagnostic."""
    if row_count == 0:
        return log_runtime_diagnostic(
            LOGGER,
            logging.INFO,
            "没有相关候选页面通过过滤，已写入空结果文件。",
            {"path": path},
        )
    return log_runtime_diagnostic(
        LOGGER,
        logging.INFO,
        "已写入接受网址结果。",
        {"path": path, "row_count": row_count},
    )


def write_accepted_url_matches_csv(path: Path, matches: list[AcceptedUrlMatch]) -> None:
    """Write final accepted URL matches to a spreadsheet-compatible CSV."""
    accepted_matches = deduplicate_accepted_url_matches(matches)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ACCEPTED_URL_FIELDNAMES)
        writer.writeheader()
        for match in accepted_matches:
            writer.writerow(
                {
                    "Source Domain": match.source_domain,
                    "Target URL": match.target_url,
                    "Detected Keyword": match.detected_keyword,
                    "Relevance Score": match.relevance_score,
                }
            )
    accepted_output_diagnostic(path, len(accepted_matches))


def write_access_reliability_csv(
    path: Path,
    rows: list[AccessReliabilitySummary],
) -> None:
    """Write access reliability rows to a spreadsheet-compatible CSV."""
    fieldnames = [
        "Success Count",
        "Success Rate",
        "Failure Count",
        "Failure Rate",
        "Failure Type",
        "Failure Type Count",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "Success Count": row.success_count,
                    "Success Rate": row.success_rate,
                    "Failure Count": row.failure_count,
                    "Failure Rate": row.failure_rate,
                    "Failure Type": row.failure_type.value,
                    "Failure Type Count": row.failure_type_count,
                }
            )

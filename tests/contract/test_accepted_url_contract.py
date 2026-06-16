"""Contract tests for accepted URL CSV output."""

import csv
from pathlib import Path

from wldm_url_filter.models import AcceptedUrlMatch
from wldm_url_filter.outputs import write_accepted_url_matches_csv


def test_accepted_url_csv_columns_are_stable(tmp_path: Path) -> None:
    path = tmp_path / "accepted.csv"

    write_accepted_url_matches_csv(
        path,
        [
            AcceptedUrlMatch(
                source_domain="example.com",
                target_url="https://example.com/guides/solar-panels",
                detected_keyword="solar panels",
                relevance_score=100,
            )
        ],
    )

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)

    assert header == [
        "Source Domain",
        "Target URL",
        "Detected Keyword",
        "Relevance Score",
    ]

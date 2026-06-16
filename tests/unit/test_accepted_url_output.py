"""Unit tests for accepted URL output generation."""

import csv
from pathlib import Path

from wldm_url_filter.models import AcceptedUrlMatch
from wldm_url_filter.outputs import (
    accepted_output_diagnostic,
    deduplicate_accepted_url_matches,
    write_accepted_url_matches_csv,
)


def test_accepted_url_csv_uses_required_columns_in_order(tmp_path: Path) -> None:
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
        assert next(reader) == [
            "Source Domain",
            "Target URL",
            "Detected Keyword",
            "Relevance Score",
        ]
        assert next(reader) == [
            "example.com",
            "https://example.com/guides/solar-panels",
            "solar panels",
            "100",
        ]


def test_deduplicate_accepted_url_matches_preserves_strongest_evidence() -> None:
    matches = [
        AcceptedUrlMatch(
            source_domain="example.com",
            target_url="https://example.com/guides/solar-panels/?b=2&a=1",
            detected_keyword="solar panels",
            relevance_score=85,
        ),
        AcceptedUrlMatch(
            source_domain="example.com",
            target_url="https://example.com/guides/solar-panels?a=1&b=2",
            detected_keyword="solar panel installation",
            relevance_score=97,
        ),
        AcceptedUrlMatch(
            source_domain="example.com",
            target_url="https://example.com/case-studies/battery-storage",
            detected_keyword="battery storage",
            relevance_score=92,
        ),
    ]

    deduplicated = deduplicate_accepted_url_matches(matches)

    assert [match.target_url for match in deduplicated] == [
        "https://example.com/guides/solar-panels?a=1&b=2",
        "https://example.com/case-studies/battery-storage",
    ]
    assert deduplicated[0].detected_keyword == "solar panel installation"
    assert deduplicated[0].relevance_score == 97


def test_write_accepted_url_matches_csv_removes_duplicate_rows(tmp_path: Path) -> None:
    path = tmp_path / "accepted.csv"
    matches = [
        AcceptedUrlMatch(
            source_domain="example.com",
            target_url="https://example.com/resources/solar/",
            detected_keyword="solar panels",
            relevance_score=90,
        ),
        AcceptedUrlMatch(
            source_domain="example.com",
            target_url="https://example.com/resources/solar",
            detected_keyword="solar panels",
            relevance_score=95,
        ),
    ]

    write_accepted_url_matches_csv(path, matches)

    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 1
    assert rows[0]["Target URL"] == "https://example.com/resources/solar"
    assert rows[0]["Relevance Score"] == "95"


def test_accepted_output_diagnostic_reports_success_and_empty_results(tmp_path: Path) -> None:
    success_message = accepted_output_diagnostic(tmp_path / "accepted.csv", 3)
    empty_message = accepted_output_diagnostic(tmp_path / "empty.csv", 0)

    assert "已写入接受网址结果" in success_message
    assert "没有相关候选页面通过过滤" in empty_message

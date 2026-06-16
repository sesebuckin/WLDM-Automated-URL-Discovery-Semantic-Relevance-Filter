"""Unit tests for shared output path handling."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from wldm_url_filter.outputs import generate_run_id, resolve_run_output_paths, validate_run_id


def test_generate_run_id_uses_utc_timestamp_format() -> None:
    run_id = generate_run_id(datetime(2026, 6, 16, 12, 30, 5, tzinfo=UTC))

    assert run_id == "20260616-123005"


def test_resolve_run_output_paths_creates_directory_and_expected_names(tmp_path: Path) -> None:
    paths = resolve_run_output_paths(tmp_path / "out", "run_001")

    assert paths.output_dir.exists()
    assert paths.accepted_urls.name == "run_001_accepted_urls.csv"
    assert paths.access_reliability.name == "run_001_access_reliability.csv"
    assert paths.processing_summary.name == "run_001_processing_summary.csv"


@pytest.mark.parametrize("run_id", ["../bad", "bad/value", "", ".hidden"])
def test_validate_run_id_rejects_path_like_values(run_id: str) -> None:
    with pytest.raises(ValueError):
        validate_run_id(run_id)

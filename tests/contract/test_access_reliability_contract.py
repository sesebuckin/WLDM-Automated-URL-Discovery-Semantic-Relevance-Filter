"""Contract tests for access reliability CSV and CLI exit behavior."""

import csv
from pathlib import Path

import respx
from httpx import Response
from typer.testing import CliRunner

from wldm_url_filter.cli import app
from wldm_url_filter.models import AccessReliabilitySummary, FailureType
from wldm_url_filter.outputs import write_access_reliability_csv


def test_access_reliability_csv_columns_are_stable(tmp_path: Path) -> None:
    path = tmp_path / "access.csv"

    write_access_reliability_csv(
        path,
        [
            AccessReliabilitySummary(
                success_count=1,
                success_rate=50.0,
                failure_count=1,
                failure_rate=50.0,
                failure_type=FailureType.TIMEOUT,
                failure_type_count=1,
            )
        ],
    )

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)

    assert header == [
        "Success Count",
        "Success Rate",
        "Failure Count",
        "Failure Rate",
        "Failure Type",
        "Failure Type Count",
    ]


def test_cli_writes_access_reliability_and_returns_optimize_again(
    tmp_path: Path,
    respx_mock: respx.MockRouter,
) -> None:
    domains = tmp_path / "domains.csv"
    keywords = tmp_path / "keywords.csv"
    output_dir = tmp_path / "output"
    domains.write_text("domain\ncli-reach.example\n", encoding="utf-8")
    keywords.write_text("keyword\nsolar panels\n", encoding="utf-8")
    respx_mock.get("https://cli-reach.example/").mock(
        return_value=Response(
            200,
            html='<a href="/blocked">Blocked</a>',
            headers={"content-type": "text/html"},
        )
    )
    respx_mock.get("https://cli-reach.example/blocked").mock(
        return_value=Response(403, headers={"content-type": "text/html"})
    )
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "run",
            "--domains",
            str(domains),
            "--keywords",
            str(keywords),
            "--output-dir",
            str(output_dir),
            "--run-id",
            "reach_contract",
        ],
    )

    access_csv = output_dir / "reach_contract_access_reliability.csv"
    assert result.exit_code == 2
    assert str(access_csv) in result.output
    assert access_csv.exists()
    assert "blocked_access" in access_csv.read_text(encoding="utf-8")


def test_cli_requester_acceptance_returns_success_for_high_failure_rate(
    tmp_path: Path,
    respx_mock: respx.MockRouter,
) -> None:
    domains = tmp_path / "domains.csv"
    keywords = tmp_path / "keywords.csv"
    output_dir = tmp_path / "output"
    domains.write_text("domain\ncli-accepted.example\n", encoding="utf-8")
    keywords.write_text("keyword\nsolar panels\n", encoding="utf-8")
    respx_mock.get("https://cli-accepted.example/").mock(
        return_value=Response(
            200,
            html='<a href="/blocked">Blocked</a>',
            headers={"content-type": "text/html"},
        )
    )
    respx_mock.get("https://cli-accepted.example/blocked").mock(
        return_value=Response(403, headers={"content-type": "text/html"})
    )
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "run",
            "--domains",
            str(domains),
            "--keywords",
            str(keywords),
            "--output-dir",
            str(output_dir),
            "--run-id",
            "reach_accepted",
            "--requester-accepted-failures",
        ],
    )

    assert result.exit_code == 0

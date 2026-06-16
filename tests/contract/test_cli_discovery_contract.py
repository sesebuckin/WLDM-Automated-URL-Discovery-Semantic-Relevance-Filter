"""CLI contract tests for discovery-only dry-run output."""

from pathlib import Path

import respx
from httpx import Response
from typer.testing import CliRunner

from wldm_url_filter.cli import app


def test_discovery_only_writes_candidate_page_csv(
    tmp_path: Path,
    respx_mock: respx.MockRouter,
) -> None:
    domains = tmp_path / "domains.csv"
    keywords = tmp_path / "keywords.csv"
    output_dir = tmp_path / "output"
    domains.write_text("domain\ncli.example\n", encoding="utf-8")
    keywords.write_text("keyword\nsolar panels\n", encoding="utf-8")
    respx_mock.get("https://cli.example/").mock(
        return_value=Response(
            200,
            html='<a href="/guides/solar-panels">Solar guide</a>',
            headers={"content-type": "text/html"},
        )
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
            "discovery_contract",
            "--discovery-only",
        ],
    )

    candidate_csv = output_dir / "discovery_contract_candidate_pages.csv"
    assert result.exit_code == 0
    assert str(candidate_csv) in result.output
    assert candidate_csv.exists()
    assert "https://cli.example/guides/solar-panels" in candidate_csv.read_text(encoding="utf-8")

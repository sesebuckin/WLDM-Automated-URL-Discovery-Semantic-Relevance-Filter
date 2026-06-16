"""End-to-end integration tests for accepted URL output generation."""

import csv
from pathlib import Path

from typer.testing import CliRunner

from wldm_url_filter import cli
from wldm_url_filter.cli import app
from wldm_url_filter.discovery import DiscoveryResult
from wldm_url_filter.models import (
    AccessOutcome,
    AccessReliabilitySummary,
    AccessStage,
    CandidatePage,
    DiscoverySource,
    FailureType,
    OptimizationStatus,
    TargetUrlAccessAttempt,
)
from wldm_url_filter.reachability import ReachabilityResult


def test_cli_writes_accepted_url_output(tmp_path: Path, monkeypatch) -> None:
    domains = tmp_path / "domains.csv"
    keywords = tmp_path / "keywords.csv"
    output_dir = tmp_path / "output"
    domains.write_text("domain\nexample.com\n", encoding="utf-8")
    keywords.write_text("keyword\nsolar panels\n", encoding="utf-8")
    candidates = [
        CandidatePage(
            source_domain="example.com",
            target_url="https://example.com/guides/solar-panels/",
            discovery_source=DiscoverySource.INTERNAL_LINK,
            url_slug="guides solar panels",
            title="Solar Panels Guide",
            primary_heading="Solar Panels",
            core_metadata="A practical installation guide.",
        ),
        CandidatePage(
            source_domain="example.com",
            target_url="https://example.com/contact",
            discovery_source=DiscoverySource.INTERNAL_LINK,
            url_slug="contact",
            title="Contact Solar Panels Team",
            primary_heading="Contact",
            utility_page_flag=True,
        ),
    ]

    def fake_discover_candidate_pages(*args, **kwargs) -> DiscoveryResult:
        return DiscoveryResult(candidates=candidates, scopes=[], diagnostics=[])

    def fake_evaluate_reachability(*args, **kwargs) -> ReachabilityResult:
        final_attempts = [
            TargetUrlAccessAttempt(
                target_url=candidate.target_url,
                stage=AccessStage.FAST_PASS,
                outcome=AccessOutcome.SUCCESS,
                failure_type=FailureType.NONE,
                status_code=200,
                elapsed_ms=10,
            )
            for candidate in candidates
        ]
        return ReachabilityResult(
            attempts=final_attempts,
            final_attempts=final_attempts,
            reliability_rows=[
                AccessReliabilitySummary(
                    success_count=2,
                    success_rate=100.0,
                    failure_count=0,
                    failure_rate=0.0,
                    failure_type=FailureType.NONE,
                    failure_type_count=0,
                )
            ],
            optimization_status=OptimizationStatus.READY,
            diagnostics=[],
        )

    monkeypatch.setattr(cli, "discover_candidate_pages", fake_discover_candidate_pages)
    monkeypatch.setattr(cli, "evaluate_reachability", fake_evaluate_reachability)
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
            "cli_output",
        ],
    )

    accepted_csv = output_dir / "cli_output_accepted_urls.csv"
    assert result.exit_code == 0
    assert str(accepted_csv) in result.output
    assert accepted_csv.exists()
    with accepted_csv.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert rows == [
        {
            "Source Domain": "example.com",
            "Target URL": "https://example.com/guides/solar-panels/",
            "Detected Keyword": "solar panels",
            "Relevance Score": "100",
        }
    ]

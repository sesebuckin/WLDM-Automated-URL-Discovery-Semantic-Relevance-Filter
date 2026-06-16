"""Contract tests for the Phase 2 CLI argument schema."""

from pathlib import Path

from typer.testing import CliRunner

from wldm_url_filter.cli import app


def test_run_command_accepts_required_and_optional_arguments(tmp_path: Path) -> None:
    domains = tmp_path / "domains.csv"
    keywords = tmp_path / "keywords.csv"
    output_dir = tmp_path / "output"
    domains.write_text("domain\nexample.com\n", encoding="utf-8")
    keywords.write_text("keyword\nsolar panels\n", encoding="utf-8")
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
            "--requester-accepted-failures",
            "--run-id",
            "contract_001",
            "--min-recall-samples",
            "3",
        ],
    )

    assert result.exit_code == 0
    assert output_dir.exists()


def test_run_command_rejects_missing_domain_file(tmp_path: Path) -> None:
    keywords = tmp_path / "keywords.csv"
    keywords.write_text("keyword\nsolar panels\n", encoding="utf-8")
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "run",
            "--domains",
            str(tmp_path / "missing.csv"),
            "--keywords",
            str(keywords),
        ],
    )

    assert result.exit_code != 0


def test_run_help_documents_contract_arguments() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["run", "--help"])

    assert result.exit_code == 0
    for option_name in [
        "--domains",
        "--keywords",
        "--output-dir",
        "--run-id",
        "--min-recall-samples",
    ]:
        assert option_name in result.output
    assert "Allow completion when" in result.output

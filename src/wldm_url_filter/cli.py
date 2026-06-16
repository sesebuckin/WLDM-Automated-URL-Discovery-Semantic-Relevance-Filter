"""Command-line entry point for the URL discovery pipeline."""

from pathlib import Path
from typing import Annotated

import typer

from wldm_url_filter.config import DEFAULT_SETTINGS
from wldm_url_filter.logging_config import configure_logging, get_logger
from wldm_url_filter.outputs import resolve_run_output_paths

app = typer.Typer(
    help="Automated URL discovery and semantic relevance filtering.",
    no_args_is_help=True,
)


@app.callback()
def callback() -> None:
    """Automated URL discovery and semantic relevance filtering."""


@app.command()
def run(
    domains: Annotated[
        Path,
        typer.Option(
            "--domains",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Path to the source domain CSV.",
        ),
    ],
    keywords: Annotated[
        Path,
        typer.Option(
            "--keywords",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Path to the target keyword CSV.",
        ),
    ],
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir",
            file_okay=False,
            dir_okay=True,
            writable=True,
            help="Directory for generated CSV outputs.",
        ),
    ] = Path("data/output"),
    requester_accepted_failures: Annotated[
        bool,
        typer.Option(
            "--requester-accepted-failures",
            help="Allow completion when final access failures remain above the target threshold.",
        ),
    ] = False,
    run_id: Annotated[
        str | None,
        typer.Option("--run-id", help="Optional stable run identifier for generated outputs."),
    ] = None,
    min_recall_samples: Annotated[
        int | None,
        typer.Option(
            "--min-recall-samples",
            min=1,
            help="Minimum depth-2 candidate count before skipping depth expansion.",
        ),
    ] = None,
) -> None:
    """Run the URL discovery and relevance filtering pipeline."""
    configure_logging()
    logger = get_logger(__name__)
    effective_min_recall_samples = min_recall_samples or DEFAULT_SETTINGS.min_recall_samples
    paths = resolve_run_output_paths(output_dir, run_id)
    logger.info("运行入口已初始化，核心流水线尚未实现。")

    _ = domains
    _ = keywords
    _ = requester_accepted_failures
    _ = effective_min_recall_samples
    _ = paths

    raise typer.Exit(code=0)


def main() -> None:
    """Invoke the Typer application."""
    app()


if __name__ == "__main__":
    main()

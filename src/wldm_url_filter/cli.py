"""Command-line entry point for the URL discovery pipeline."""

from pathlib import Path
from typing import Annotated

import typer

from wldm_url_filter.config import DEFAULT_SETTINGS
from wldm_url_filter.discovery import discover_candidate_pages
from wldm_url_filter.ingestion import load_source_domains, load_target_keywords
from wldm_url_filter.logging_config import configure_logging, get_logger
from wldm_url_filter.outputs import resolve_run_output_paths, write_candidate_pages_csv

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
    discovery_only: Annotated[
        bool,
        typer.Option(
            "--discovery-only",
            help="Run candidate discovery only and write the candidate-page dry-run CSV.",
        ),
    ] = False,
) -> None:
    """Run the URL discovery and relevance filtering pipeline."""
    configure_logging()
    logger = get_logger(__name__)
    effective_min_recall_samples = min_recall_samples or DEFAULT_SETTINGS.min_recall_samples
    paths = resolve_run_output_paths(output_dir, run_id)
    settings = DEFAULT_SETTINGS.__class__(
        fast_pass_timeout_seconds=DEFAULT_SETTINGS.fast_pass_timeout_seconds,
        timeout_retest_seconds=DEFAULT_SETTINGS.timeout_retest_seconds,
        fast_pass_concurrency=DEFAULT_SETTINGS.fast_pass_concurrency,
        timeout_retest_concurrency=DEFAULT_SETTINGS.timeout_retest_concurrency,
        max_pages_per_domain=DEFAULT_SETTINGS.max_pages_per_domain,
        initial_crawl_depth=DEFAULT_SETTINGS.initial_crawl_depth,
        expanded_crawl_depth=DEFAULT_SETTINGS.expanded_crawl_depth,
        min_recall_samples=effective_min_recall_samples,
        target_failure_rate=DEFAULT_SETTINGS.target_failure_rate,
    )

    if discovery_only:
        source_domains = load_source_domains(domains)
        target_keywords = load_target_keywords(keywords)
        result = discover_candidate_pages(source_domains, target_keywords, settings=settings)
        write_candidate_pages_csv(paths.candidate_pages, result.candidates)
        logger.info("候选页面发现完成，已写入发现结果。")
        typer.echo(str(paths.candidate_pages))
        raise typer.Exit(code=0)

    logger.info("运行入口已初始化，核心流水线尚未实现。")

    _ = domains
    _ = keywords
    _ = requester_accepted_failures
    _ = effective_min_recall_samples
    _ = discovery_only
    _ = paths

    raise typer.Exit(code=0)


def main() -> None:
    """Invoke the Typer application."""
    app()


if __name__ == "__main__":
    main()

"""Runtime configuration defaults for the URL discovery pipeline."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RuntimeSettings:
    """Shared runtime settings used by pipeline services."""

    fast_pass_timeout_seconds: float = 5.0
    timeout_retest_seconds: float = 20.0
    fast_pass_concurrency: int = 50
    timeout_retest_concurrency: int = 1
    max_pages_per_domain: int = 50
    initial_crawl_depth: int = 2
    expanded_crawl_depth: int = 3
    min_recall_samples: int = 1
    target_failure_rate: float = 0.10


DEFAULT_SETTINGS = RuntimeSettings()

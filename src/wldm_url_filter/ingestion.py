"""CSV ingestion helpers for source domains and target keywords."""

from __future__ import annotations

import csv
import re
from collections.abc import Iterable
from pathlib import Path

from wldm_url_filter.config import UnsafeUrlError, normalize_domain_value
from wldm_url_filter.models import SourceDomain, TargetKeyword, ValidationStatus

_DOMAIN_COLUMNS = {
    "domain",
    "source_domain",
    "source domain",
    "root_domain",
    "root domain",
    "url",
    "website",
}
_KEYWORD_COLUMNS = {"keyword", "target_keyword", "target keyword", "term", "niche"}
_GROUP_COLUMNS = {"group", "keyword_group", "keyword group", "category"}


def load_source_domains(path: Path) -> list[SourceDomain]:
    """Load, normalize, validate, and duplicate-mark source domains from CSV."""
    rows = _read_csv_rows(path)
    if not rows:
        return []

    headers = rows[0]
    column_index = infer_csv_column(headers, _DOMAIN_COLUMNS)
    seen_domains: set[str] = set()
    domains: list[SourceDomain] = []

    for row_number, row in _iter_data_rows(rows):
        raw_value = _cell_at(row, column_index)
        try:
            normalized_domain = normalize_domain_value(raw_value)
        except UnsafeUrlError as exc:
            domains.append(
                SourceDomain(
                    raw_value=raw_value,
                    input_row_number=row_number,
                    validation_status=ValidationStatus.INVALID,
                    validation_reason=str(exc),
                )
            )
            continue

        if normalized_domain in seen_domains:
            domains.append(
                SourceDomain(
                    raw_value=raw_value,
                    normalized_domain=normalized_domain,
                    input_row_number=row_number,
                    validation_status=ValidationStatus.DUPLICATE,
                    validation_reason="Duplicate domain",
                )
            )
            continue

        seen_domains.add(normalized_domain)
        domains.append(
            SourceDomain(
                raw_value=raw_value,
                normalized_domain=normalized_domain,
                input_row_number=row_number,
                validation_status=ValidationStatus.VALID,
            )
        )

    return domains


def load_target_keywords(path: Path) -> list[TargetKeyword]:
    """Load target keywords from CSV, ignoring blank and duplicate normalized values."""
    rows = _read_csv_rows(path)
    if not rows:
        return []

    headers = rows[0]
    keyword_index = infer_csv_column(headers, _KEYWORD_COLUMNS)
    group_index = infer_optional_csv_column(headers, _GROUP_COLUMNS)
    seen_keywords: set[str] = set()
    keywords: list[TargetKeyword] = []

    for _, row in _iter_data_rows(rows):
        keyword = _cell_at(row, keyword_index).strip()
        normalized_keyword = normalize_keyword(keyword)
        if not normalized_keyword or normalized_keyword in seen_keywords:
            continue

        seen_keywords.add(normalized_keyword)
        keyword_group = _cell_at(row, group_index).strip() if group_index is not None else None
        keywords.append(
            TargetKeyword(
                keyword=keyword,
                normalized_keyword=normalized_keyword,
                keyword_group=keyword_group or None,
            )
        )

    return keywords


def infer_csv_column(headers: Iterable[str], accepted_names: set[str]) -> int:
    """Infer the relevant CSV column by accepted header names, falling back to the first column."""
    normalized_headers = [_normalize_header(header) for header in headers]
    for index, header in enumerate(normalized_headers):
        if header in accepted_names:
            return index
    return 0


def infer_optional_csv_column(headers: Iterable[str], accepted_names: set[str]) -> int | None:
    """Infer an optional CSV column by accepted header names."""
    normalized_headers = [_normalize_header(header) for header in headers]
    for index, header in enumerate(normalized_headers):
        if header in accepted_names:
            return index
    return None


def normalize_keyword(keyword: str) -> str:
    """Normalize a target keyword for duplicate detection and matching."""
    return re.sub(r"\s+", " ", keyword.strip().lower())


def _read_csv_rows(path: Path) -> list[list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.reader(handle))


def _iter_data_rows(rows: list[list[str]]) -> Iterable[tuple[int, list[str]]]:
    yield from enumerate(rows[1:], start=2)


def _cell_at(row: list[str], index: int) -> str:
    if index >= len(row):
        return ""
    return row[index]


def _normalize_header(header: str) -> str:
    return re.sub(r"\s+", " ", header.strip().lower().replace("-", "_"))

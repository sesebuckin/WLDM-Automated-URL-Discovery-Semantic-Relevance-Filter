"""Unit tests for CSV ingestion."""

from pathlib import Path

from wldm_url_filter.ingestion import load_source_domains, load_target_keywords
from wldm_url_filter.models import ValidationStatus


def test_load_source_domains_infers_domain_column_and_marks_duplicates(tmp_path: Path) -> None:
    csv_path = tmp_path / "domains.csv"
    csv_path.write_text(
        "name,source_domain\n"
        "first,HTTPS://Example.com/path\n"
        "duplicate,example.com/\n"
        "unsafe,localhost\n"
        "blank,\n",
        encoding="utf-8",
    )

    domains = load_source_domains(csv_path)

    assert [domain.validation_status for domain in domains] == [
        ValidationStatus.VALID,
        ValidationStatus.DUPLICATE,
        ValidationStatus.INVALID,
        ValidationStatus.INVALID,
    ]
    assert domains[0].normalized_domain == "example.com"


def test_load_source_domains_falls_back_to_first_column(tmp_path: Path) -> None:
    csv_path = tmp_path / "domains.csv"
    csv_path.write_text("Website Name,notes\nwww.Example.org/a,ok\n", encoding="utf-8")

    domains = load_source_domains(csv_path)

    assert domains[0].normalized_domain == "example.org"


def test_load_target_keywords_ignores_blanks_and_duplicates(tmp_path: Path) -> None:
    csv_path = tmp_path / "keywords.csv"
    csv_path.write_text(
        "group,target_keyword\n"
        "energy,Solar Panels\n"
        "energy, solar   panels \n"
        "waste,\n"
        "water,Heat Pump\n",
        encoding="utf-8",
    )

    keywords = load_target_keywords(csv_path)

    assert [keyword.normalized_keyword for keyword in keywords] == ["solar panels", "heat pump"]
    assert keywords[0].keyword_group == "energy"

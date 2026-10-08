from pathlib import Path

import pytest

from src.transformation.staging import read_sql_file


def test_read_sql_file(tmp_path):
    path = tmp_path / "query.sql"
    path.write_text("SELECT 1;", encoding="utf-8")

    assert read_sql_file(path) == "SELECT 1;"


def test_missing_sql_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_sql_file(tmp_path / "missing.sql")


def test_empty_sql_file(tmp_path):
    path = tmp_path / "empty.sql"
    path.write_text("   ", encoding="utf-8")

    with pytest.raises(ValueError):
        read_sql_file(path)


def test_staging_schema_exists():
    assert Path("sql/staging/001_create_staging_schema.sql").is_file()


def test_transformation_sql_exists():
    assert Path("sql/staging/002_populate_staging.sql").is_file()


def test_quality_sql_exists():
    assert Path("sql/quality/001_quality_checks.sql").is_file()
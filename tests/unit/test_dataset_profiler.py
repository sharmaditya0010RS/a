
import json

import pytest

from src.profiling.dataset_profiler import (
    file_checksum,
    inspect_csv,
    write_markdown_reports,
    write_profile,
)


@pytest.fixture
def sample_csv(tmp_path):
    path = tmp_path / "transactions.csv"

    path.write_text(
        "Timestamp,Amount,Sender,Is Laundering\n"
        "2024-01-01 10:00:00,100.50,A,0\n"
        "2024-01-01 11:00:00,200.00,B,1\n"
        "2024-01-01 12:00:00,,C,0\n",
        encoding="utf-8",
    )

    return path


def test_file_checksum(sample_csv):
    checksum = file_checksum(sample_csv)

    assert len(checksum) == 64
    assert checksum == file_checksum(sample_csv)


def test_profile_row_and_column_counts(sample_csv):
    profile = inspect_csv(sample_csv, chunk_size=2)

    assert profile["row_count"] == 3
    assert profile["column_count"] == 4


def test_profile_missing_values(sample_csv):
    profile = inspect_csv(sample_csv, chunk_size=2)

    amount = next(
        field
        for field in profile["field_profiles"]
        if field["column"] == "Amount"
    )

    assert amount["missing_count"] == 1
    assert amount["nonempty_count"] == 2


def test_profile_numeric_inference(sample_csv):
    profile = inspect_csv(sample_csv, chunk_size=2)

    amount = next(
        field
        for field in profile["field_profiles"]
        if field["column"] == "Amount"
    )

    assert amount["inferred_type"] == "decimal_candidate"


def test_invalid_chunk_size(sample_csv):
    with pytest.raises(ValueError):
        inspect_csv(sample_csv, chunk_size=0)


def test_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        inspect_csv(tmp_path / "missing.csv")


def test_write_outputs(sample_csv, tmp_path):
    profile = inspect_csv(sample_csv, chunk_size=2)

    json_path = tmp_path / "profile.json"
    report_path = tmp_path / "report.md"
    dictionary_path = tmp_path / "dictionary.md"

    write_profile(profile, json_path)

    write_markdown_reports(
        profile,
        report_path,
        dictionary_path,
    )

    saved = json.loads(json_path.read_text(encoding="utf-8"))

    assert saved["row_count"] == 3
    assert report_path.exists()
    assert dictionary_path.exists()
    assert "Amount" in dictionary_path.read_text(
        encoding="utf-8"
    )

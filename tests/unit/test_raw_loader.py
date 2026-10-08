
import csv
import io

import pytest

from src.ingestion.raw_loader import (
    build_copy_buffer,
    normalize_row,
)


@pytest.fixture
def sample_row():
    return [
        "2022/09/01 00:00",
        "001",
        "800042CB0",
        "002",
        "800052F90",
        "100.25",
        "US Dollar",
        "100.25",
        "US Dollar",
        "ACH",
        "1",
    ]


def test_normalize_row_preserves_identifiers(sample_row):
    normalized = normalize_row(sample_row, "batch-1", 1)

    assert normalized[3] == "001"
    assert normalized[4] == "800042CB0"
    assert normalized[5] == "002"
    assert normalized[6] == "800052F90"


def test_normalize_row_preserves_decimal_amounts(sample_row):
    normalized = normalize_row(sample_row, "batch-1", 1)

    assert normalized[7] == "100.25"
    assert normalized[9] == "100.25"


def test_normalize_row_generates_hash(sample_row):
    normalized = normalize_row(sample_row, "batch-1", 1)

    assert len(normalized[13]) == 64


def test_invalid_timestamp(sample_row):
    sample_row[0] = "not-a-date"

    with pytest.raises(ValueError):
        normalize_row(sample_row, "batch-1", 1)


def test_invalid_label(sample_row):
    sample_row[10] = "2"

    with pytest.raises(ValueError):
        normalize_row(sample_row, "batch-1", 1)


def test_invalid_amount(sample_row):
    sample_row[5] = "invalid"

    with pytest.raises(ValueError):
        normalize_row(sample_row, "batch-1", 1)


def test_missing_bank(sample_row):
    sample_row[1] = ""

    with pytest.raises(ValueError):
        normalize_row(sample_row, "batch-1", 1)


def test_copy_buffer(sample_row):
    normalized = normalize_row(sample_row, "batch-1", 1)
    buffer = build_copy_buffer([normalized])

    parsed = list(csv.reader(io.StringIO(buffer.getvalue())))

    assert len(parsed) == 1
    assert parsed[0] == normalized


import json

import pytest

from src.profiling.source_audit import (
    audit_source,
    parse_amount,
    save_audit,
)


@pytest.fixture
def audit_csv(tmp_path):
    path = tmp_path / "sample.csv"

    path.write_text(
        "Timestamp,From Bank,Account,To Bank,Account,"
        "Amount Received,Receiving Currency,Amount Paid,"
        "Payment Currency,Payment Format,Is Laundering\n"
        "2022/09/01 00:00,001,A,002,B,100,US Dollar,"
        "100,US Dollar,ACH,0\n"
        "2022/09/01 00:01,001,A,001,A,0,US Dollar,"
        "0,US Dollar,Cash,1\n"
        "2022/09/01 00:01,001,A,001,A,0,US Dollar,"
        "0,US Dollar,Cash,1\n",
        encoding="utf-8",
    )

    return path


def test_parse_amount():
    assert str(parse_amount("100.25")) == "100.25"
    assert parse_amount("invalid") is None
    assert parse_amount("NaN") is None


def test_audit_counts(audit_csv, tmp_path):
    result = audit_source(
        audit_csv,
        tmp_path / "index.sqlite",
        batch_size=2,
    )

    assert result["row_count"] == 3
    assert result["duplicate_fingerprint_candidates"] == 1
    assert result["unique_row_fingerprints"] == 2
    assert result["aml_label_distribution"] == {
        "0": 1,
        "1": 2,
    }


def test_audit_dates_and_accounts(audit_csv, tmp_path):
    result = audit_source(
        audit_csv,
        tmp_path / "index.sqlite",
    )

    assert result["earliest_timestamp"] == "2022-09-01 00:00:00"
    assert result["latest_timestamp"] == "2022-09-01 00:01:00"
    assert result["same_account_transaction_count"] == 2
    assert result["zero_amount_counts"]["Amount Paid"] == 2


def test_audit_rejects_existing_index(audit_csv, tmp_path):
    index = tmp_path / "index.sqlite"
    index.write_bytes(b"existing")

    with pytest.raises(FileExistsError):
        audit_source(audit_csv, index)


def test_audit_rejects_bad_header(tmp_path):
    source = tmp_path / "bad.csv"
    source.write_text("Wrong,Header\n1,2\n", encoding="utf-8")

    with pytest.raises(ValueError):
        audit_source(source, tmp_path / "index.sqlite")


def test_save_audit(tmp_path):
    destination = tmp_path / "result.json"

    save_audit({"row_count": 3}, destination)

    result = json.loads(
        destination.read_text(encoding="utf-8")
    )

    assert result["row_count"] == 3


import csv
import hashlib
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

EXPECTED_COLUMNS = [
    "Timestamp",
    "From Bank",
    "Account",
    "To Bank",
    "Account",
    "Amount Received",
    "Receiving Currency",
    "Amount Paid",
    "Payment Currency",
    "Payment Format",
    "Is Laundering",
]


def parse_amount(value: str) -> Decimal | None:
    try:
        amount = Decimal(value.strip())
    except InvalidOperation:
        return None

    if not amount.is_finite():
        return None

    return amount


def row_fingerprint(row: list[str]) -> bytes:
    payload = json.dumps(
        row,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(payload).digest()


def audit_source(
    source_path: str | Path,
    index_path: str | Path,
    batch_size: int = 10000,
) -> dict:
    source = Path(source_path)
    index = Path(index_path)

    if not source.is_file():
        raise FileNotFoundError(source)

    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    index.parent.mkdir(parents=True, exist_ok=True)

    if index.exists():
        raise FileExistsError(
            f"Duplicate index already exists: {index}"
        )

    row_count = 0
    duplicate_candidates = 0
    invalid_timestamps = 0
    invalid_amounts = Counter()
    negative_amounts = Counter()
    zero_amounts = Counter()
    label_counts = Counter()
    payment_formats = Counter()
    receiving_currencies = Counter()
    payment_currencies = Counter()
    same_bank_count = 0
    same_account_count = 0
    earliest = None
    latest = None

    connection = sqlite3.connect(index)

    try:
        connection.execute(
            "CREATE TABLE row_hashes (digest BLOB PRIMARY KEY)"
        )

        with source.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as stream:
            reader = csv.reader(stream)
            header = next(reader, None)

            if header != EXPECTED_COLUMNS:
                raise ValueError(
                    f"Unexpected CSV header: {header}"
                )

            pending = []

            def flush_hashes() -> int:
                if not pending:
                    return 0

                before = connection.total_changes

                connection.executemany(
                    "INSERT OR IGNORE INTO row_hashes VALUES (?)",
                    pending,
                )

                inserted = connection.total_changes - before
                duplicates = len(pending) - inserted
                pending.clear()

                return duplicates

            for row in reader:
                if len(row) != len(EXPECTED_COLUMNS):
                    raise ValueError(
                        f"Invalid field count at data row {row_count + 1}"
                    )

                row_count += 1

                pending.append((row_fingerprint(row),))

                if len(pending) >= batch_size:
                    duplicate_candidates += flush_hashes()

                timestamp = row[0].strip()

                try:
                    parsed_time = datetime.strptime(
                        timestamp,
                        "%Y/%m/%d %H:%M",
                    )

                    if earliest is None or parsed_time < earliest:
                        earliest = parsed_time

                    if latest is None or parsed_time > latest:
                        latest = parsed_time

                except ValueError:
                    invalid_timestamps += 1

                if row[1] == row[3]:
                    same_bank_count += 1

                if (
                    row[1] == row[3]
                    and row[2] == row[4]
                ):
                    same_account_count += 1

                receiving_currencies[row[6]] += 1
                payment_currencies[row[8]] += 1
                payment_formats[row[9]] += 1
                label_counts[row[10]] += 1

                for name, position in [
                    ("Amount Received", 5),
                    ("Amount Paid", 7),
                ]:
                    amount = parse_amount(row[position])

                    if amount is None:
                        invalid_amounts[name] += 1
                    elif amount < 0:
                        negative_amounts[name] += 1
                    elif amount == 0:
                        zero_amounts[name] += 1

            duplicate_candidates += flush_hashes()

        connection.commit()

    finally:
        connection.close()

    return {
        "dataset_name": source.name,
        "audited_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "row_count": row_count,
        "duplicate_fingerprint_candidates": duplicate_candidates,
        "unique_row_fingerprints": (
            row_count - duplicate_candidates
        ),
        "earliest_timestamp": (
            earliest.isoformat(sep=" ")
            if earliest is not None
            else None
        ),
        "latest_timestamp": (
            latest.isoformat(sep=" ")
            if latest is not None
            else None
        ),
        "invalid_timestamp_count": invalid_timestamps,
        "invalid_amount_counts": dict(invalid_amounts),
        "negative_amount_counts": dict(negative_amounts),
        "zero_amount_counts": dict(zero_amounts),
        "aml_label_distribution": dict(
            sorted(label_counts.items())
        ),
        "payment_format_distribution": dict(
            sorted(payment_formats.items())
        ),
        "receiving_currency_distribution": dict(
            sorted(receiving_currencies.items())
        ),
        "payment_currency_distribution": dict(
            sorted(payment_currencies.items())
        ),
        "same_bank_transaction_count": same_bank_count,
        "same_account_transaction_count": same_account_count,
        "limitations": [
            "Duplicate candidates are based on SHA-256 row fingerprints.",
            "Repeated source rows are not automatically invalid.",
            "Timestamp timezone is unknown.",
            "AML labels are synthetic annotations.",
            "Same-account matching uses bank and account identifiers.",
            "Monetary totals across currencies are not calculated.",
        ],
    }


def save_audit(result: dict, destination: str | Path) -> None:
    output = Path(destination)
    output.parent.mkdir(parents=True, exist_ok=True)

    output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

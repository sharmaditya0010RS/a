
import csv
import hashlib
import io
import json
import uuid
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from sqlalchemy import create_engine, text

from src.profiling.dataset_profiler import file_checksum

EXPECTED_HEADER = [
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


COPY_COLUMNS = [
    "batch_id",
    "source_row_number",
    "transaction_timestamp",
    "from_bank",
    "from_account",
    "to_bank",
    "to_account",
    "amount_received",
    "receiving_currency",
    "amount_paid",
    "payment_currency",
    "payment_format",
    "is_laundering",
    "row_sha256",
]


def normalize_row(
    row: list[str],
    batch_id: str,
    source_row_number: int,
) -> list[str]:
    if len(row) != 11:
        raise ValueError(
            f"Invalid column count at source row {source_row_number}"
        )

    try:
        timestamp = datetime.strptime(
            row[0].strip(),
            "%Y/%m/%d %H:%M",
        )
    except ValueError as error:
        raise ValueError(
            f"Invalid timestamp at source row {source_row_number}"
        ) from error

    amounts = []

    for position in (5, 7):
        try:
            amount = Decimal(row[position].strip())
        except InvalidOperation as error:
            raise ValueError(
                f"Invalid amount at source row {source_row_number}"
            ) from error

        if not amount.is_finite() or amount <= 0:
            raise ValueError(
                f"Non-positive amount at source row {source_row_number}"
            )

        amounts.append(str(amount))

    if row[10] not in {"0", "1"}:
        raise ValueError(
            f"Invalid AML label at source row {source_row_number}"
        )

    required_positions = (1, 2, 3, 4, 6, 8, 9)

    if any(not row[position].strip() for position in required_positions):
        raise ValueError(
            f"Missing required field at source row {source_row_number}"
        )

    digest = hashlib.sha256(
        json.dumps(
            row,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    return [
        batch_id,
        str(source_row_number),
        timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        row[1],
        row[2],
        row[3],
        row[4],
        amounts[0],
        row[6],
        amounts[1],
        row[8],
        row[9],
        row[10],
        digest,
    ]


def build_copy_buffer(rows: list[list[str]]) -> io.StringIO:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")

    writer.writerows(rows)
    buffer.seek(0)

    return buffer


def get_raw_connection(database_url: str):
    engine = create_engine(database_url)

    connection = engine.raw_connection()

    return engine, connection


def load_raw_dataset(
    database_url: str,
    source_path: str | Path,
    schema_path: str | Path,
    expected_rows: int,
    chunk_size: int = 50000,
) -> dict:
    source = Path(source_path)

    if not source.is_file():
        raise FileNotFoundError(source)

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    if expected_rows < 0:
        raise ValueError("expected_rows cannot be negative")

    source_sha256 = file_checksum(source)
    batch_id = str(uuid.uuid4())

    engine = create_engine(database_url)

    try:
        with engine.begin() as connection:
            connection.exec_driver_sql(
                Path(schema_path).read_text(encoding="utf-8")
            )

            existing = connection.execute(
                text(
                    "SELECT batch_id, status, loaded_rows "
                    "FROM raw.ingestion_batches "
                    "WHERE source_sha256 = :checksum"
                ),
                {"checksum": source_sha256},
            ).mappings().first()

            if existing is not None:
                if existing["status"] == "completed":
                    return {
                        "status": "already_loaded",
                        "batch_id": str(existing["batch_id"]),
                        "loaded_rows": existing["loaded_rows"],
                        "source_sha256": source_sha256,
                    }

                raise RuntimeError(
                    "A previous incomplete batch exists for this checksum"
                )

            connection.execute(
                text(
                    "INSERT INTO raw.ingestion_batches "
                    "(batch_id, source_filename, source_sha256, "
                    "status, expected_rows) "
                    "VALUES (:batch_id, :filename, :checksum, "
                    "'running', :expected_rows)"
                ),
                {
                    "batch_id": batch_id,
                    "filename": source.name,
                    "checksum": source_sha256,
                    "expected_rows": expected_rows,
                },
            )

        loaded_rows = 0

        with source.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as stream:
            reader = csv.reader(stream)
            header = next(reader, None)

            if header != EXPECTED_HEADER:
                raise ValueError(
                    f"Unexpected source CSV header: {header}"
                )

            while True:
                chunk = []

                for _ in range(chunk_size):
                    row = next(reader, None)

                    if row is None:
                        break

                    source_row_number = loaded_rows + len(chunk) + 1

                    chunk.append(
                        normalize_row(
                            row,
                            batch_id,
                            source_row_number,
                        )
                    )

                if not chunk:
                    break

                buffer = build_copy_buffer(chunk)

                raw_connection = engine.raw_connection()

                try:
                    cursor = raw_connection.cursor()

                    try:
                        copy_statement = (
                            "COPY raw.transactions ("
                            + ", ".join(COPY_COLUMNS)
                            + ") FROM STDIN WITH (FORMAT CSV)"
                        )

                        with cursor.copy(copy_statement) as copy:
                            copy.write(buffer.getvalue())

                        cursor.execute(
                            "UPDATE raw.ingestion_batches "
                            "SET loaded_rows = %s "
                            "WHERE batch_id = %s",
                            (
                                loaded_rows + len(chunk),
                                batch_id,
                            ),
                        )

                        raw_connection.commit()

                    finally:
                        cursor.close()

                except Exception:
                    raw_connection.rollback()
                    raise

                finally:
                    raw_connection.close()

                loaded_rows += len(chunk)

                print(
                    f"Loaded {loaded_rows:,} / "
                    f"{expected_rows:,} rows"
                )

        if loaded_rows != expected_rows:
            raise ValueError(
                f"Expected {expected_rows:,} rows, "
                f"loaded {loaded_rows:,}"
            )

        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE raw.ingestion_batches "
                    "SET status = 'completed', "
                    "completed_at = NOW() "
                    "WHERE batch_id = :batch_id"
                ),
                {"batch_id": batch_id},
            )

        return {
            "status": "completed",
            "batch_id": batch_id,
            "loaded_rows": loaded_rows,
            "source_sha256": source_sha256,
        }

    except Exception as error:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE raw.ingestion_batches "
                    "SET status = 'failed', "
                    "error_message = :message, "
                    "completed_at = NOW() "
                    "WHERE batch_id = :batch_id "
                    "AND status = 'running'"
                ),
                {
                    "batch_id": batch_id,
                    "message": str(error)[:2000],
                },
            )

        raise

    finally:
        engine.dispose()

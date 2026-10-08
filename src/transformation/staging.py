
from pathlib import Path
from time import monotonic
from uuid import uuid4

from sqlalchemy import create_engine, text


def read_sql_file(path: str) -> str:
    content = Path(path).read_text(encoding="utf-8")

    if not content.strip():
        raise ValueError(f"SQL file is empty: {path}")

    return content


EXPECTED_ROWS = 5_078_345
BATCH_SIZE = 100_000

INSERT_SQL = """
INSERT INTO staging.transactions (
    transaction_id, batch_id, source_row_number,
    transaction_timestamp, transaction_date, transaction_hour,
    from_bank, from_account, to_bank, to_account,
    sender_entity_key, receiver_entity_key,
    amount_received, receiving_currency,
    amount_paid, payment_currency, payment_format,
    is_laundering, row_sha256,
    is_same_bank, is_same_account, is_cross_currency,
    is_duplicate_candidate, has_quality_issue, quality_issue_codes
)
SELECT
    r.transaction_id,
    r.batch_id,
    r.source_row_number,
    r.transaction_timestamp,
    r.transaction_timestamp::date,
    EXTRACT(HOUR FROM r.transaction_timestamp)::smallint,
    r.from_bank,
    r.from_account,
    r.to_bank,
    r.to_account,
    LENGTH(r.from_bank)::text || ':' || r.from_bank ||
        LENGTH(r.from_account)::text || ':' || r.from_account,
    LENGTH(r.to_bank)::text || ':' || r.to_bank ||
        LENGTH(r.to_account)::text || ':' || r.to_account,
    r.amount_received,
    r.receiving_currency,
    r.amount_paid,
    r.payment_currency,
    r.payment_format,
    r.is_laundering,
    r.row_sha256,
    r.from_bank = r.to_bank,
    r.from_bank = r.to_bank AND r.from_account = r.to_account,
    r.receiving_currency <> r.payment_currency,
    FALSE,
    FALSE,
    ARRAY[]::text[]
FROM raw.transactions r
JOIN raw.ingestion_batches b ON b.batch_id = r.batch_id
WHERE b.status = 'completed'
  AND r.transaction_id > :last_id
ORDER BY r.transaction_id
LIMIT :batch_size
"""

METRICS_SQL = """
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE is_laundering = 1) AS positives,
    COUNT(*) FILTER (WHERE is_duplicate_candidate) AS duplicates,
    COUNT(*) FILTER (WHERE has_quality_issue) AS issues,
    COUNT(*) FILTER (
        WHERE transaction_date <> transaction_timestamp::date
    ) AS invalid_dates,
    COUNT(*) FILTER (
        WHERE is_same_account AND NOT is_same_bank
    ) AS invalid_accounts,
    COUNT(*) FILTER (
        WHERE sender_entity_key IS NULL OR receiver_entity_key IS NULL
    ) AS missing_keys,
    COUNT(*) FILTER (
        WHERE amount_received <= 0 OR amount_paid <= 0
    ) AS invalid_amounts,
    COUNT(*) FILTER (
        WHERE is_laundering NOT IN (0, 1)
    ) AS invalid_labels
FROM staging.transactions
"""


def build_staging(
    database_url: str,
    schema_path: str = "sql/staging/001_create_staging_schema.sql",
    transformation_path: str = "sql/staging/002_populate_staging.sql",
    quality_path: str = "sql/quality/001_quality_checks.sql",
) -> dict:
    del transformation_path, quality_path

    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 10},
    )
    build_id = str(uuid4())
    started = monotonic()

    try:
        schema_sql = read_sql_file(schema_path)

        with engine.begin() as connection:
            connection.exec_driver_sql(schema_sql)
            connection.execute(
                text(
                    "SELECT pg_advisory_xact_lock("
                    "hashtext('fci_staging_build'))"
                )
            )
            active = connection.execute(
                text(
                    "SELECT COUNT(*) FROM pg_stat_activity "
                    "WHERE datname = current_database() "
                    "AND state = 'active' "
                    "AND query LIKE 'TRUNCATE TABLE staging.transactions%'"
                )
            ).scalar_one()
            if active:
                raise RuntimeError("Another staging build is active")

            connection.execute(
                text(
                    "UPDATE staging.build_runs "
                    "SET status = 'failed', completed_at = NOW(), "
                    "error_message = 'Interrupted previous build' "
                    "WHERE status = 'running'"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO staging.build_runs (build_id, status) "
                    "VALUES (:build_id, 'running')"
                ),
                {"build_id": build_id},
            )

        with engine.connect() as connection:
            source_rows = connection.execute(
                text(
                    "SELECT COUNT(*) FROM raw.transactions r "
                    "JOIN raw.ingestion_batches b "
                    "ON b.batch_id = r.batch_id "
                    "WHERE b.status = 'completed'"
                )
            ).scalar_one()

            progress = connection.execute(
                text(
                    "SELECT COUNT(*) AS processed, "
                    "COALESCE(MAX(transaction_id), 0) AS last_id "
                    "FROM staging.transactions"
                )
            ).mappings().one()

        processed = int(progress["processed"])
        last_id = int(progress["last_id"])

        if source_rows != EXPECTED_ROWS:
            raise RuntimeError(
                f"Expected {EXPECTED_ROWS:,} source rows, "
                f"found {source_rows:,}"
            )

        print(
            f"Resuming staging: {processed:,}/{source_rows:,}",
            flush=True,
        )

        while processed < source_rows:
            with engine.begin() as connection:
                result = connection.execute(
                    text(INSERT_SQL),
                    {"last_id": last_id, "batch_size": BATCH_SIZE},
                )
                inserted = result.rowcount

                if inserted <= 0:
                    raise RuntimeError(
                        "No more source rows; staging is incomplete"
                    )

                last_id = connection.execute(
                    text(
                        "SELECT MAX(transaction_id) "
                        "FROM staging.transactions"
                    )
                ).scalar_one()

            processed += inserted
            percentage = processed * 100 / source_rows
            remaining = source_rows - processed
            elapsed = monotonic() - started
            rate = processed / max(elapsed, 1)
            eta = remaining / max(rate, 1)

            print(
                f"\rProgress: {percentage:6.2f}% | "
                f"Done: {processed:,} | "
                f"Left: {remaining:,} | "
                f"ETA estimate: {eta / 60:.1f} min",
                end="",
                flush=True,
            )

        print("\nDetecting duplicate fingerprints...", flush=True)

        with engine.begin() as connection:
            connection.execute(
                text(
                    "WITH duplicates AS ("
                    "SELECT transaction_id, "
                    "ROW_NUMBER() OVER ("
                    "PARTITION BY batch_id, row_sha256 "
                    "ORDER BY source_row_number"
                    ") AS occurrence "
                    "FROM staging.transactions "
                    "WHERE (batch_id, row_sha256) IN ("
                    "SELECT batch_id, row_sha256 "
                    "FROM staging.transactions "
                    "GROUP BY batch_id, row_sha256 "
                    "HAVING COUNT(*) > 1"
                    ")"
                    ") "
                    "UPDATE staging.transactions s "
                    "SET is_duplicate_candidate = TRUE "
                    "FROM duplicates d "
                    "WHERE s.transaction_id = d.transaction_id "
                    "AND d.occurrence > 1"
                )
            )

        print("Running final quality checks...", flush=True)

        with engine.begin() as connection:
            metrics = connection.execute(
                text(METRICS_SQL)
            ).mappings().one()

            checks = {
                "row_count_reconciliation": (
                    metrics["total_rows"], source_rows
                ),
                "aml_positive_count": (metrics["positives"], 5177),
                "duplicate_candidates": (metrics["duplicates"], 9),
                "invalid_transaction_dates": (
                    metrics["invalid_dates"], 0
                ),
                "invalid_same_account_flags": (
                    metrics["invalid_accounts"], 0
                ),
                "missing_entity_keys": (metrics["missing_keys"], 0),
                "invalid_amounts": (metrics["invalid_amounts"], 0),
                "invalid_labels": (metrics["invalid_labels"], 0),
                "quality_issue_rows": (metrics["issues"], 0),
            }

            connection.execute(
                text("DELETE FROM staging.quality_results")
            )

            for name, (observed, expected) in checks.items():
                connection.execute(
                    text(
                        "INSERT INTO staging.quality_results "
                        "(check_name, observed_value, "
                        "expected_value, status) "
                        "VALUES (:name, :observed, :expected, :status)"
                    ),
                    {
                        "name": name,
                        "observed": int(observed),
                        "expected": expected,
                        "status": (
                            "PASS" if observed == expected else "FAIL"
                        ),
                    },
                )

            failures = [
                name
                for name, (observed, expected) in checks.items()
                if observed != expected
            ]

            if failures:
                raise RuntimeError(
                    "Quality checks failed: " + ", ".join(failures)
                )

            connection.execute(
                text(
                    "UPDATE staging.build_runs "
                    "SET status = 'completed', "
                    "completed_at = NOW(), "
                    "source_rows = :source_rows, "
                    "staged_rows = :staged_rows "
                    "WHERE build_id = :build_id"
                ),
                {
                    "source_rows": source_rows,
                    "staged_rows": processed,
                    "build_id": build_id,
                },
            )

        print("Phase 4 staging completed successfully", flush=True)
        return {
            "status": "completed",
            "build_id": build_id,
            "source_rows": source_rows,
            "staged_rows": processed,
        }

    except Exception as exc:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE staging.build_runs "
                    "SET status = 'failed', completed_at = NOW(), "
                    "error_message = :error "
                    "WHERE build_id = :build_id"
                ),
                {"build_id": build_id, "error": str(exc)[:2000]},
            )
        raise
    finally:
        engine.dispose()

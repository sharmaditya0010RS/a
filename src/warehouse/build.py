import time
from pathlib import Path

from sqlalchemy import create_engine, text

from src.common.config import get_settings

BATCH_SIZE = 100_000

DIMENSIONS = [
    """
    INSERT INTO warehouse.dim_date
        (date_key, full_date, calendar_year, calendar_month,
         calendar_day, calendar_quarter, day_of_week, is_weekend)
    SELECT DISTINCT
        TO_CHAR(transaction_date, 'YYYYMMDD')::INTEGER,
        transaction_date,
        EXTRACT(YEAR FROM transaction_date)::SMALLINT,
        EXTRACT(MONTH FROM transaction_date)::SMALLINT,
        EXTRACT(DAY FROM transaction_date)::SMALLINT,
        EXTRACT(QUARTER FROM transaction_date)::SMALLINT,
        EXTRACT(ISODOW FROM transaction_date)::SMALLINT,
        EXTRACT(ISODOW FROM transaction_date) IN (6, 7)
    FROM staging.transactions
    WHERE transaction_id > :low AND transaction_id <= :high
    ON CONFLICT DO NOTHING
    """,
    """
    INSERT INTO warehouse.dim_entity (entity_key, bank_id, account_id)
    SELECT DISTINCT sender_entity_key, from_bank, from_account
    FROM staging.transactions
    WHERE transaction_id > :low AND transaction_id <= :high
    ON CONFLICT DO NOTHING
    """,
    """
    INSERT INTO warehouse.dim_entity (entity_key, bank_id, account_id)
    SELECT DISTINCT receiver_entity_key, to_bank, to_account
    FROM staging.transactions
    WHERE transaction_id > :low AND transaction_id <= :high
    ON CONFLICT DO NOTHING
    """,
    """
    INSERT INTO warehouse.dim_currency (currency_key)
    SELECT DISTINCT receiving_currency
    FROM staging.transactions
    WHERE transaction_id > :low AND transaction_id <= :high
    ON CONFLICT DO NOTHING
    """,
    """
    INSERT INTO warehouse.dim_currency (currency_key)
    SELECT DISTINCT payment_currency
    FROM staging.transactions
    WHERE transaction_id > :low AND transaction_id <= :high
    ON CONFLICT DO NOTHING
    """,
    """
    INSERT INTO warehouse.dim_payment_format (payment_format_key)
    SELECT DISTINCT payment_format
    FROM staging.transactions
    WHERE transaction_id > :low AND transaction_id <= :high
    ON CONFLICT DO NOTHING
    """,
]

FACT_SQL = """
INSERT INTO warehouse.fact_transactions (
    transaction_id, date_key, sender_entity_key, receiver_entity_key,
    receiving_currency_key, payment_currency_key, payment_format_key,
    transaction_timestamp, amount_received, amount_paid, is_laundering,
    is_same_bank, is_same_account, is_cross_currency,
    is_duplicate_candidate
)
SELECT
    transaction_id,
    TO_CHAR(transaction_date, 'YYYYMMDD')::INTEGER,
    sender_entity_key,
    receiver_entity_key,
    receiving_currency,
    payment_currency,
    payment_format,
    transaction_timestamp,
    amount_received,
    amount_paid,
    is_laundering,
    is_same_bank,
    is_same_account,
    is_cross_currency,
    is_duplicate_candidate
FROM staging.transactions
WHERE transaction_id > :low AND transaction_id <= :high
ORDER BY transaction_id
ON CONFLICT (transaction_id) DO NOTHING
"""

MART_SQL = """
INSERT INTO warehouse.mart_daily_aml (
    date_key, transaction_count, aml_positive_count,
    total_amount_paid, cross_currency_count,
    duplicate_candidate_count, refreshed_at
)
SELECT
    date_key,
    COUNT(*),
    COUNT(*) FILTER (WHERE is_laundering = 1),
    SUM(amount_paid),
    COUNT(*) FILTER (WHERE is_cross_currency),
    COUNT(*) FILTER (WHERE is_duplicate_candidate),
    NOW()
FROM warehouse.fact_transactions
GROUP BY date_key
ON CONFLICT (date_key) DO UPDATE SET
    transaction_count = EXCLUDED.transaction_count,
    aml_positive_count = EXCLUDED.aml_positive_count,
    total_amount_paid = EXCLUDED.total_amount_paid,
    cross_currency_count = EXCLUDED.cross_currency_count,
    duplicate_candidate_count = EXCLUDED.duplicate_candidate_count,
    refreshed_at = NOW()
"""


def build_warehouse(database_url: str, batch_size: int = BATCH_SIZE) -> dict:
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    engine = create_engine(database_url, pool_pre_ping=True)
    started = time.monotonic()

    try:
        with engine.begin() as connection:
            schema_sql = Path(
                "sql/warehouse/001_create_warehouse.sql"
            ).read_text(encoding="utf-8-sig")
            connection.exec_driver_sql(schema_sql)

        with engine.connect() as connection:
            source_rows = connection.execute(
                text("SELECT COUNT(*) FROM staging.transactions")
            ).scalar_one()
            staged_rows = connection.execute(
                text("SELECT COUNT(*) FROM warehouse.fact_transactions")
            ).scalar_one()
            last_id = connection.execute(
                text(
                    "SELECT COALESCE(MAX(transaction_id), 0) "
                    "FROM warehouse.fact_transactions"
                )
            ).scalar_one()

        print(
            f"Resuming warehouse: {staged_rows:,}/{source_rows:,}",
            flush=True,
        )

        while staged_rows < source_rows:
            with engine.begin() as connection:
                upper = connection.execute(
                    text(
                        "SELECT transaction_id "
                        "FROM staging.transactions "
                        "WHERE transaction_id > :last_id "
                        "ORDER BY transaction_id "
                        "LIMIT 1 OFFSET :offset"
                    ),
                    {"last_id": last_id, "offset": batch_size - 1},
                ).scalar_one_or_none()

                if upper is None:
                    upper = connection.execute(
                        text(
                            "SELECT MAX(transaction_id) "
                            "FROM staging.transactions "
                            "WHERE transaction_id > :last_id"
                        ),
                        {"last_id": last_id},
                    ).scalar_one_or_none()

                if upper is None:
                    break

                params = {"low": last_id, "high": upper}

                for statement in DIMENSIONS:
                    connection.execute(text(statement), params)

                inserted = connection.execute(
                    text(FACT_SQL), params
                ).rowcount

            last_id = upper
            staged_rows += inserted
            elapsed = max(time.monotonic() - started, 0.001)
            rate = inserted if elapsed <= 0 else staged_rows / elapsed
            remaining = max(source_rows - staged_rows, 0)
            eta = remaining / max(rate, 0.001) / 60

            print(
                f"Progress: {staged_rows / source_rows * 100:6.2f}% "
                f"| Done: {staged_rows:,} "
                f"| Left: {remaining:,} "
                f"| ETA estimate: {eta:.1f} min",
                flush=True,
            )

        with engine.connect() as connection:
            final_count = connection.execute(
                text("SELECT COUNT(*) FROM warehouse.fact_transactions")
            ).scalar_one()

        if final_count != source_rows:
            raise RuntimeError(
                f"Warehouse reconciliation failed: "
                f"source={source_rows}, fact={final_count}"
            )

        print("Refreshing daily AML mart...", flush=True)

        with engine.begin() as connection:
            connection.execute(text(MART_SQL))

        result = {
            "status": "completed",
            "source_rows": source_rows,
            "fact_rows": final_count,
        }
        print(f"Phase 5 warehouse completed: {result}", flush=True)
        return result
    finally:
        engine.dispose()


if __name__ == "__main__":
    build_warehouse(get_settings().database_url)

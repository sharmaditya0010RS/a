from sqlalchemy import create_engine, text

from src.common.config import get_settings

checks = {
    "fact_row_count": (
        "SELECT COUNT(*) FROM warehouse.fact_transactions",
        5078345,
    ),
    "aml_positive_count": (
        "SELECT COUNT(*) FROM warehouse.fact_transactions "
        "WHERE is_laundering = 1",
        5177,
    ),
    "duplicate_candidates": (
        "SELECT COUNT(*) FROM warehouse.fact_transactions "
        "WHERE is_duplicate_candidate",
        9,
    ),
    "mart_transaction_count": (
        "SELECT COALESCE(SUM(transaction_count), 0) "
        "FROM warehouse.mart_daily_aml",
        5078345,
    ),
    "mart_aml_positive_count": (
        "SELECT COALESCE(SUM(aml_positive_count), 0) "
        "FROM warehouse.mart_daily_aml",
        5177,
    ),
    "mart_duplicate_count": (
        "SELECT COALESCE(SUM(duplicate_candidate_count), 0) "
        "FROM warehouse.mart_daily_aml",
        9,
    ),
    "orphan_sender_keys": (
        "SELECT COUNT(*) FROM warehouse.fact_transactions f "
        "LEFT JOIN warehouse.dim_entity d "
        "ON f.sender_entity_key = d.entity_key "
        "WHERE d.entity_key IS NULL",
        0,
    ),
    "orphan_receiver_keys": (
        "SELECT COUNT(*) FROM warehouse.fact_transactions f "
        "LEFT JOIN warehouse.dim_entity d "
        "ON f.receiver_entity_key = d.entity_key "
        "WHERE d.entity_key IS NULL",
        0,
    ),
}

engine = create_engine(get_settings().database_url)
failures = []

try:
    with engine.connect() as connection:
        for name, (query, expected) in checks.items():
            actual = connection.execute(text(query)).scalar_one()
            status = "PASS" if actual == expected else "FAIL"
            print(f"{status}: {name} = {actual:,}")
            if actual != expected:
                failures.append(name)

        print("\nDIMENSION COUNTS:")
        for table in (
            "dim_date",
            "dim_entity",
            "dim_currency",
            "dim_payment_format",
        ):
            count = connection.execute(
                text(f"SELECT COUNT(*) FROM warehouse.{table}")
            ).scalar_one()
            print(f"{table}: {count:,}")
            if count == 0:
                failures.append(table)
finally:
    engine.dispose()

if failures:
    raise SystemExit(f"WAREHOUSE VALIDATION FAILED: {failures}")

print("\nPHASE 5 WAREHOUSE VALIDATION PASSED")

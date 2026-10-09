from pathlib import Path

from sqlalchemy import create_engine, text

from src.common.config import get_settings


def main() -> None:
    engine = create_engine(get_settings().database_url, pool_pre_ping=True)

    try:
        with engine.begin() as connection:
            schema = Path(
                "sql/risk/001_create_risk_schema.sql"
            ).read_text(encoding="utf-8-sig")
            connection.exec_driver_sql(schema)

        print("Risk schema created.", flush=True)
        print("Calculating currency-specific P99 thresholds...", flush=True)

        with engine.begin() as connection:
            thresholds = Path(
                "sql/risk/002_currency_thresholds.sql"
            ).read_text(encoding="utf-8-sig")
            connection.exec_driver_sql(thresholds)

        with engine.connect() as connection:
            count = connection.execute(
                text("SELECT COUNT(*) FROM risk.currency_thresholds")
            ).scalar_one()

        print(f"Currency thresholds calculated: {count}", flush=True)
        print("PHASE 6 RISK SETUP PASSED", flush=True)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()

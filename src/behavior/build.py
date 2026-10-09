import time
from pathlib import Path

from sqlalchemy import create_engine, text

from src.common.config import get_settings


def build_daily_activity() -> None:
    engine = create_engine(
        get_settings().database_url,
        pool_pre_ping=True,
    )

    schema_sql = Path(
        "sql/behavior/001_create_behavior_schema.sql"
    ).read_text(encoding="utf-8-sig")

    build_sql = Path(
        "sql/behavior/002_build_daily_activity.sql"
    ).read_text(encoding="utf-8-sig")

    try:
        with engine.begin() as connection:
            connection.exec_driver_sql(schema_sql)

        with engine.connect() as connection:
            dates = connection.execute(
                text(
                    "SELECT DISTINCT date_key "
                    "FROM warehouse.fact_transactions "
                    "ORDER BY date_key"
                )
            ).scalars().all()

        total = len(dates)
        print(f"Dates to process: {total}", flush=True)

        for index, date_key in enumerate(dates, start=1):
            with engine.connect() as connection:
                existing = connection.execute(
                    text(
                        "SELECT EXISTS ("
                        "SELECT 1 FROM behavior.entity_daily_activity "
                        "WHERE date_key = :date_key"
                        ")"
                    ),
                    {"date_key": date_key},
                ).scalar_one()

            if existing:
                print(
                    f"[{index}/{total}] SKIP date_key={date_key}",
                    flush=True,
                )
                continue

            started = time.monotonic()

            with engine.begin() as connection:
                connection.execute(
                    text(build_sql),
                    {"date_key": date_key},
                )

            elapsed = time.monotonic() - started

            with engine.connect() as connection:
                rows = connection.execute(
                    text(
                        "SELECT COUNT(*) "
                        "FROM behavior.entity_daily_activity "
                        "WHERE date_key = :date_key"
                    ),
                    {"date_key": date_key},
                ).scalar_one()

            print(
                f"[{index}/{total}] "
                f"date_key={date_key} "
                f"entities={rows:,} "
                f"elapsed={elapsed:.1f}s",
                flush=True,
            )

        with engine.connect() as connection:
            total_rows = connection.execute(
                text(
                    "SELECT COUNT(*) "
                    "FROM behavior.entity_daily_activity"
                )
            ).scalar_one()

        print(
            f"Entity daily activity rows: {total_rows:,}",
            flush=True,
        )
        print("PHASE 7 DAILY ACTIVITY BUILD PASSED", flush=True)
    finally:
        engine.dispose()


if __name__ == "__main__":
    build_daily_activity()

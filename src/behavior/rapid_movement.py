import time
from pathlib import Path

from sqlalchemy import create_engine, text

from src.common.config import get_settings


def read_sql(filename: str) -> str:
    return Path("sql/behavior", filename).read_text(
        encoding="utf-8-sig"
    )


def build_rapid_movement() -> None:
    engine = create_engine(
        get_settings().database_url,
        pool_pre_ping=True,
    )

    try:
        with engine.begin() as connection:
            connection.exec_driver_sql(
                read_sql("005_create_rapid_movement.sql")
            )

        print("Creating receiver timestamp index...", flush=True)

        with engine.begin() as connection:
            connection.exec_driver_sql(
                read_sql("007_rapid_movement_index.sql")
            )

        print("Index ready.", flush=True)

        with engine.connect() as connection:
            dates = connection.execute(
                text(
                    "SELECT DISTINCT date_key "
                    "FROM warehouse.fact_transactions "
                    "ORDER BY date_key"
                )
            ).scalars().all()

        query = text(read_sql("006_build_rapid_movement.sql"))
        total = len(dates)

        for index, date_key in enumerate(dates, start=1):
            started = time.monotonic()

            with engine.begin() as connection:
                result = connection.execute(
                    query,
                    {"date_key": date_key},
                )
                inserted = result.rowcount

            elapsed = time.monotonic() - started

            print(
                f"[{index}/{total}] "
                f"date_key={date_key} "
                f"new_pairs={inserted:,} "
                f"elapsed={elapsed:.1f}s",
                flush=True,
            )

        with engine.connect() as connection:
            total_pairs = connection.execute(
                text(
                    "SELECT COUNT(*) "
                    "FROM behavior.rapid_movement"
                )
            ).scalar_one()

        print(f"Rapid movement pairs: {total_pairs:,}", flush=True)
        print("PHASE 7 RAPID MOVEMENT BUILD PASSED", flush=True)
    finally:
        engine.dispose()


if __name__ == "__main__":
    build_rapid_movement()

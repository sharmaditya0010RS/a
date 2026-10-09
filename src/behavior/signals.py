import time
from pathlib import Path

from sqlalchemy import create_engine, text

from src.common.config import get_settings


def build_behavior_signals() -> None:
    engine = create_engine(
        get_settings().database_url,
        pool_pre_ping=True,
    )

    schema_sql = Path(
        "sql/behavior/003_create_signals.sql"
    ).read_text(encoding="utf-8-sig")

    build_sql = Path(
        "sql/behavior/004_build_signals.sql"
    ).read_text(encoding="utf-8-sig")

    try:
        with engine.begin() as connection:
            connection.exec_driver_sql(schema_sql)

        with engine.connect() as connection:
            dates = connection.execute(
                text(
                    "SELECT DISTINCT date_key "
                    "FROM behavior.entity_daily_activity "
                    "ORDER BY date_key"
                )
            ).scalars().all()

        total = len(dates)
        print(f"Dates to score: {total}", flush=True)

        for index, date_key in enumerate(dates, start=1):
            started = time.monotonic()

            with engine.begin() as connection:
                connection.execute(
                    text(build_sql),
                    {"date_key": date_key},
                )

            elapsed = time.monotonic() - started

            print(
                f"[{index}/{total}] "
                f"date_key={date_key} "
                f"elapsed={elapsed:.1f}s",
                flush=True,
            )

        with engine.connect() as connection:
            scored = connection.execute(
                text(
                    "SELECT COUNT(*) "
                    "FROM behavior.entity_daily_signals"
                )
            ).scalar_one()

            source = connection.execute(
                text(
                    "SELECT COUNT(*) "
                    "FROM behavior.entity_daily_activity"
                )
            ).scalar_one()

        print(f"Source entity-days: {source:,}", flush=True)
        print(f"Scored entity-days: {scored:,}", flush=True)

        if scored != source:
            raise RuntimeError(
                f"Behavior reconciliation failed: "
                f"source={source}, scored={scored}"
            )

        print("PHASE 7 BEHAVIOR SIGNALS PASSED", flush=True)
    finally:
        engine.dispose()


if __name__ == "__main__":
    build_behavior_signals()

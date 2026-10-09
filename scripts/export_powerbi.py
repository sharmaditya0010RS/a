import csv
from pathlib import Path

from sqlalchemy import create_engine, text

from src.common.config import get_settings

OUTPUT = Path("exports/powerbi")

DATASETS = {
    "executive_kpis": """
        SELECT * FROM analytics.vw_executive_kpis
    """,
    "daily_risk_trends": """
        SELECT * FROM analytics.vw_daily_risk_trends
        ORDER BY full_date
    """,
    "detection_effectiveness": """
        SELECT * FROM analytics.vw_detection_effectiveness
    """,
    "investigation_queue": """
        SELECT * FROM analytics.vw_investigation_queue
        ORDER BY risk_score DESC, alert_id
    """,
    "entity_risk_leaderboard": """
        SELECT *
        FROM analytics.vw_entity_risk_leaderboard
        WHERE entity_risk_level IN ('HIGH', 'CRITICAL')
        ORDER BY entity_risk_score DESC, entity_key
    """,
}


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)

    engine = create_engine(
        get_settings().database_url,
        pool_pre_ping=True,
    )

    try:
        with engine.connect() as connection:
            for name, sql in DATASETS.items():
                path = OUTPUT / f"{name}.csv"
                result = connection.execution_options(
                    stream_results=True
                ).execute(text(sql))

                count = 0

                with path.open(
                    "w",
                    newline="",
                    encoding="utf-8-sig",
                ) as file:
                    writer = csv.writer(file)
                    writer.writerow(result.keys())

                    for row in result:
                        writer.writerow(row)
                        count += 1

                print(
                    f"EXPORTED {name}: {count:,} rows",
                    flush=True,
                )

        print("PHASE 8 POWER BI EXPORT PASSED", flush=True)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()

from pathlib import Path

from sqlalchemy import create_engine, text

from src.common.config import get_settings


def main() -> None:
    engine = create_engine(
        get_settings().database_url,
        pool_pre_ping=True,
    )

    sql = Path(
        "sql/analytics/001_create_reporting_views.sql"
    ).read_text(encoding="utf-8-sig")

    try:
        with engine.begin() as connection:
            connection.exec_driver_sql(sql)

        print("Analytics reporting views deployed.", flush=True)

        with engine.connect() as connection:
            kpis = connection.execute(
                text("SELECT * FROM analytics.vw_executive_kpis")
            ).mappings().one()

            print("\nEXECUTIVE KPIs:", flush=True)
            for key, value in kpis.items():
                print(f"{key}: {value}", flush=True)

            effectiveness = connection.execute(
                text(
                    "SELECT * "
                    "FROM analytics.vw_detection_effectiveness"
                )
            ).mappings().one()

            print("\nDETECTION EFFECTIVENESS:", flush=True)
            for key, value in effectiveness.items():
                print(f"{key}: {value}", flush=True)

            daily_count = connection.execute(
                text(
                    "SELECT COUNT(*) "
                    "FROM analytics.vw_daily_risk_trends"
                )
            ).scalar_one()

            queue_count = connection.execute(
                text(
                    "SELECT COUNT(*) "
                    "FROM analytics.vw_investigation_queue"
                )
            ).scalar_one()

            entity_count = connection.execute(
                text(
                    "SELECT COUNT(*) "
                    "FROM analytics.vw_entity_risk_leaderboard"
                )
            ).scalar_one()

            print("\nREPORTING VALIDATION:", flush=True)

            checks = {
                "daily_trend_dates": daily_count == 18,
                "investigation_queue": (
                    queue_count == kpis["total_alerts"]
                ),
                "entity_leaderboard": (
                    entity_count == kpis["total_entities"]
                ),
                "transaction_count": (
                    kpis["total_transactions"] == 5_078_345
                ),
                "aml_positive_count": (
                    kpis["aml_positive_transactions"] == 5_177
                ),
                "confusion_matrix_reconciliation": (
                    effectiveness["true_positives"]
                    + effectiveness["false_positives"]
                    + effectiveness["false_negatives"]
                    + effectiveness["true_negatives"]
                    == kpis["total_transactions"]
                ),
            }

            for name, passed in checks.items():
                print(
                    f"{'PASS' if passed else 'FAIL'}: {name}",
                    flush=True,
                )

            if not all(checks.values()):
                raise RuntimeError(
                    "Analytics reporting validation failed"
                )

        print(
            "\nPHASE 8 ANALYTICS LAYER PASSED",
            flush=True,
        )
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()

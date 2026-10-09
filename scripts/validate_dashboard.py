from sqlalchemy import create_engine, text

from src.common.config import get_settings


def main() -> None:
    engine = create_engine(
        get_settings().database_url,
        pool_pre_ping=True,
    )

    checks = {
        "fact_score_reconciliation": """
            SELECT
                (SELECT COUNT(*)
                 FROM warehouse.fact_transactions)
                =
                (SELECT COUNT(*)
                 FROM risk.transaction_scores)
        """,
        "entity_daily_reconciliation": """
            SELECT
                (SELECT COUNT(*)
                 FROM behavior.entity_daily_activity)
                =
                (SELECT COUNT(*)
                 FROM behavior.entity_daily_signals)
        """,
        "advanced_daily_reconciliation": """
            SELECT
                (SELECT COUNT(*)
                 FROM behavior.entity_daily_activity)
                =
                (SELECT COUNT(*)
                 FROM behavior.entity_daily_advanced)
        """,
        "entity_profile_reconciliation": """
            SELECT
                (SELECT COUNT(*)
                 FROM warehouse.dim_entity)
                =
                (SELECT COUNT(*)
                 FROM behavior.entity_risk_profiles)
        """,
        "rapid_movement_reconciliation": """
            SELECT
                (SELECT COUNT(*)
                 FROM behavior.rapid_movement)
                =
                (SELECT COALESCE(SUM(rapid_movement_count), 0)
                 FROM behavior.entity_daily_advanced)
        """,
        "alert_count_reconciliation": """
            SELECT
                (SELECT COUNT(*)
                 FROM risk.alerts)
                =
                (SELECT total_alerts
                 FROM analytics.vw_executive_kpis)
        """,
        "daily_mart_reconciliation": """
            SELECT NOT EXISTS (
                SELECT 1
                FROM analytics.vw_daily_risk_trends t
                JOIN warehouse.mart_daily_aml m
                  ON m.date_key =
                     CAST(
                         TO_CHAR(t.full_date, 'YYYYMMDD')
                         AS INTEGER
                     )
                WHERE t.transaction_count <> m.transaction_count
                   OR t.aml_positive_count <> m.aml_positive_count
            )
        """,
        "confusion_matrix_reconciliation": """
            SELECT
                (
                    true_positives
                    + false_positives
                    + false_negatives
                    + true_negatives
                ) =
                (
                    SELECT COUNT(*)
                    FROM warehouse.fact_transactions
                )
            FROM analytics.vw_detection_effectiveness
        """,
        "alert_rule_explainability": """
            SELECT NOT EXISTS (
                SELECT 1
                FROM risk.alerts a
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM risk.rule_hits h
                    WHERE h.transaction_id = a.transaction_id
                )
            )
        """,
        "invalid_entity_risk_classification": """
            SELECT NOT EXISTS (
                SELECT 1
                FROM behavior.entity_risk_profiles
                WHERE entity_risk_level <> CASE
                    WHEN entity_risk_score >= 80 THEN 'CRITICAL'
                    WHEN entity_risk_score >= 50 THEN 'HIGH'
                    WHEN entity_risk_score >= 25 THEN 'MEDIUM'
                    ELSE 'LOW'
                END
            )
        """,
    }

    failures = []

    try:
        with engine.connect() as connection:
            for name, sql in checks.items():
                result = connection.execute(
                    text(sql)
                ).scalar_one()

                passed = result is True

                print(
                    f"{'PASS' if passed else 'FAIL'}: {name}",
                    flush=True,
                )

                if not passed:
                    failures.append(name)

        print(
            f"\nValidation: "
            f"{len(checks) - len(failures)}/{len(checks)} PASS",
            flush=True,
        )

        if failures:
            raise RuntimeError(
                f"Dashboard validation failed: {failures}"
            )

        print(
            "PHASE 8 DASHBOARD DATA VALIDATION PASSED",
            flush=True,
        )

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
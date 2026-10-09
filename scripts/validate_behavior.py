from sqlalchemy import create_engine, text

from src.common.config import get_settings


def validate_behavior() -> None:
    engine = create_engine(
        get_settings().database_url,
        pool_pre_ping=True,
    )

    checks = {
        "source_score_reconciliation": """
            SELECT (
                (SELECT COUNT(*) FROM behavior.entity_daily_activity)
                -
                (SELECT COUNT(*) FROM behavior.entity_daily_signals)
            )
        """,
        "missing_scored_entity_days": """
            SELECT COUNT(*)
            FROM behavior.entity_daily_activity a
            LEFT JOIN behavior.entity_daily_signals s
              ON a.entity_key = s.entity_key
             AND a.date_key = s.date_key
            WHERE s.entity_key IS NULL
        """,
        "orphan_scored_entity_days": """
            SELECT COUNT(*)
            FROM behavior.entity_daily_signals s
            LEFT JOIN behavior.entity_daily_activity a
              ON s.entity_key = a.entity_key
             AND s.date_key = a.date_key
            WHERE a.entity_key IS NULL
        """,
        "invalid_score_ranges": """
            SELECT COUNT(*)
            FROM behavior.entity_daily_signals
            WHERE behavior_score NOT BETWEEN 0 AND 100
        """,
        "incorrect_risk_levels": """
            SELECT COUNT(*)
            FROM behavior.entity_daily_signals
            WHERE behavior_level <> CASE
                WHEN behavior_score >= 80 THEN 'CRITICAL'
                WHEN behavior_score >= 50 THEN 'HIGH'
                WHEN behavior_score >= 25 THEN 'MEDIUM'
                ELSE 'LOW'
            END
        """,
        "incorrect_signal_scores": """
            SELECT COUNT(*)
            FROM behavior.entity_daily_signals
            WHERE behavior_score <> (
                CASE WHEN velocity_flag THEN 30 ELSE 0 END
                + CASE WHEN fan_in_flag THEN 25 ELSE 0 END
                + CASE WHEN fan_out_flag THEN 25 ELSE 0 END
                + CASE WHEN cross_currency_flag THEN 10 ELSE 0 END
                + CASE WHEN high_value_flag THEN 10 ELSE 0 END
            )
        """,
        "incorrect_activity_flags": """
            SELECT COUNT(*)
            FROM behavior.entity_daily_signals s
            JOIN behavior.entity_daily_activity a
              ON s.entity_key = a.entity_key
             AND s.date_key = a.date_key
            WHERE s.velocity_flag IS DISTINCT FROM
                    (a.outgoing_count >= 20)
               OR s.fan_in_flag IS DISTINCT FROM
                    (a.distinct_senders >= 10)
               OR s.fan_out_flag IS DISTINCT FROM
                    (a.distinct_receivers >= 10)
               OR s.cross_currency_flag IS DISTINCT FROM
                    (a.cross_currency_outgoing >= 5)
               OR s.high_value_flag IS DISTINCT FROM
                    (a.high_value_outgoing >= 3)
        """,
    }

    try:
        with engine.connect() as connection:
            failures = []

            for name, query in checks.items():
                value = connection.execute(text(query)).scalar_one()
                status = "PASS" if value == 0 else "FAIL"
                print(f"{status}: {name} = {value:,}", flush=True)

                if value != 0:
                    failures.append(name)

            print("\nBEHAVIOR RISK DISTRIBUTION:", flush=True)

            for level, count in connection.execute(
                text(
                    "SELECT behavior_level, COUNT(*) "
                    "FROM behavior.entity_daily_signals "
                    "GROUP BY behavior_level "
                    "ORDER BY behavior_level"
                )
            ):
                print(f"{level}: {count:,}", flush=True)

            print("\nBEHAVIOR SIGNAL COUNTS:", flush=True)

            counts = connection.execute(
                text(
                    "SELECT "
                    "COUNT(*) FILTER (WHERE velocity_flag), "
                    "COUNT(*) FILTER (WHERE fan_in_flag), "
                    "COUNT(*) FILTER (WHERE fan_out_flag), "
                    "COUNT(*) FILTER (WHERE cross_currency_flag), "
                    "COUNT(*) FILTER (WHERE high_value_flag) "
                    "FROM behavior.entity_daily_signals"
                )
            ).one()

            names = (
                "VELOCITY",
                "FAN_IN",
                "FAN_OUT",
                "CROSS_CURRENCY",
                "HIGH_VALUE",
            )

            for name, count in zip(names, counts, strict=True):
                print(f"{name}: {count:,}", flush=True)

            if failures:
                raise RuntimeError(
                    f"Behavior validation failed: {failures}"
                )

            print(
                "\nPHASE 7 BEHAVIOR VALIDATION PASSED",
                flush=True,
            )
    finally:
        engine.dispose()


if __name__ == "__main__":
    validate_behavior()

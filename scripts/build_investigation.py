from pathlib import Path

from sqlalchemy import create_engine, text

from src.common.config import get_settings

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SQL_FILE = (
    PROJECT_ROOT
    / "sql"
    / "investigation"
    / "001_prioritized_alerts.sql"
)


def main() -> None:
    if not SQL_FILE.exists():
        raise FileNotFoundError(
            f"Missing SQL file: {SQL_FILE}"
        )

    engine = create_engine(
        get_settings().database_url,
        pool_pre_ping=True,
    )

    try:
        with engine.begin() as conn:
            print("Checking source integrity...")

            source_check = conn.execute(
                text(
                    """
                    SELECT
                        (SELECT COUNT(*)
                         FROM risk.alerts) AS alert_count,

                        (SELECT COUNT(*)
                         FROM (
                             SELECT transaction_id
                             FROM warehouse.fact_transactions
                             GROUP BY transaction_id
                             HAVING COUNT(*) > 1
                         ) AS duplicates) AS duplicate_fact_ids,

                        (SELECT COUNT(*)
                         FROM (
                             SELECT entity_key
                             FROM behavior.entity_risk_profiles
                             GROUP BY entity_key
                             HAVING COUNT(*) > 1
                         ) AS duplicates) AS duplicate_entity_keys,

                        (SELECT COUNT(*)
                         FROM risk.alerts AS a
                         LEFT JOIN warehouse.fact_transactions AS f
                           ON f.transaction_id = a.transaction_id
                         WHERE f.transaction_id IS NULL
                        ) AS unmatched_alerts
                    """
                )
            ).mappings().one()

            if source_check["duplicate_fact_ids"]:
                raise RuntimeError(
                    "Duplicate transaction IDs detected "
                    "in warehouse.fact_transactions."
                )

            if source_check["duplicate_entity_keys"]:
                raise RuntimeError(
                    "Duplicate entity keys detected "
                    "in behavior.entity_risk_profiles."
                )

            if source_check["unmatched_alerts"]:
                raise RuntimeError(
                    "Some alerts do not match warehouse "
                    "transactions."
                )

            print("Creating investigation view...")

            conn.exec_driver_sql(
                SQL_FILE.read_text(encoding="utf-8")
            )

            print("Validating priority scores...")

            validation = conn.execute(
                text(
                    """
                    SELECT
                        COUNT(*) AS prioritized_alerts,

                        COUNT(DISTINCT alert_id)
                            AS unique_alert_ids,

                        COUNT(*) FILTER (
                            WHERE investigation_priority_score
                                NOT BETWEEN 0 AND 100
                        ) AS invalid_scores,

                        COUNT(*) FILTER (
                            WHERE priority_tier NOT IN (
                                'P1', 'P2', 'P3', 'P4'
                            )
                        ) AS invalid_tiers,

                        COUNT(*) FILTER (
                            WHERE
                                (
                                    investigation_priority_score >= 80
                                    AND priority_tier <> 'P1'
                                )
                                OR
                                (
                                    investigation_priority_score
                                        BETWEEN 65 AND 79
                                    AND priority_tier <> 'P2'
                                )
                                OR
                                (
                                    investigation_priority_score
                                        BETWEEN 50 AND 64
                                    AND priority_tier <> 'P3'
                                )
                                OR
                                (
                                    investigation_priority_score < 50
                                    AND priority_tier <> 'P4'
                                )
                        ) AS tier_mismatches

                    FROM investigation.vw_prioritized_alerts
                    """
                )
            ).mappings().one()

            expected = int(source_check["alert_count"])
            actual = int(validation["prioritized_alerts"])

            if actual != expected:
                raise RuntimeError(
                    f"Alert reconciliation failed: "
                    f"{actual:,} != {expected:,}"
                )

            if int(validation["unique_alert_ids"]) != expected:
                raise RuntimeError(
                    "Investigation view contains duplicate alert IDs."
                )

            if int(validation["invalid_scores"]):
                raise RuntimeError(
                    "Investigation priority scores outside 0–100."
                )

            if int(validation["invalid_tiers"]):
                raise RuntimeError(
                    "Unexpected investigation priority tier."
                )

            if int(validation["tier_mismatches"]):
                raise RuntimeError(
                    "Priority tiers do not match score thresholds."
                )

            print(
                f"PASS: {actual:,} alerts reconciled."
            )

            print("\nPriority distribution:")

            distribution = conn.execute(
                text(
                    """
                    SELECT
                        priority_tier,
                        COUNT(*) AS alert_count,
                        MIN(investigation_priority_score)
                            AS minimum_score,
                        MAX(investigation_priority_score)
                            AS maximum_score

                    FROM investigation.vw_prioritized_alerts

                    GROUP BY priority_tier

                    ORDER BY priority_tier
                    """
                )
            ).mappings()

            for row in distribution:
                print(
                    f"{row['priority_tier']}: "
                    f"{row['alert_count']:,} alerts "
                    f"(scores {row['minimum_score']}–"
                    f"{row['maximum_score']})"
                )

            print(
                "\nPHASE 9 STEP 1: "
                "INVESTIGATION PRIORITY VIEW PASSED"
            )

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
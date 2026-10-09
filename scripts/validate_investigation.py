from __future__ import annotations

from sqlalchemy import create_engine, text

from src.common.config import get_settings


def main() -> None:
    engine = create_engine(
        get_settings().database_url,
        pool_pre_ping=True,
    )

    checks: dict[str, bool] = {}

    try:
        with engine.connect() as connection:
            summary = connection.execute(
                text(
                    """
                    SELECT
                        COUNT(*) AS total,
                        COUNT(DISTINCT alert_id) AS unique_alerts,

                        COUNT(*) FILTER (
                            WHERE investigation_priority_score
                                NOT BETWEEN 0 AND 100
                        ) AS invalid_scores,

                        COUNT(*) FILTER (
                            WHERE investigation_priority_score
                                IS NULL
                        ) AS missing_scores,

                        COUNT(*) FILTER (
                            WHERE priority_tier NOT IN (
                                'P1', 'P2', 'P3', 'P4'
                            )
                            OR priority_tier IS NULL
                        ) AS invalid_tiers,

                        COUNT(*) FILTER (
                            WHERE investigation_priority_score
                                <> transaction_component
                                + entity_component
                                + dual_high_risk_component
                        ) AS component_mismatches,

                        COUNT(*) FILTER (
                            WHERE
                                priority_tier <>
                                CASE
                                    WHEN investigation_priority_score >= 80
                                        THEN 'P1'
                                    WHEN investigation_priority_score >= 65
                                        THEN 'P2'
                                    WHEN investigation_priority_score >= 50
                                        THEN 'P3'
                                    ELSE 'P4'
                                END
                        ) AS tier_mismatches

                    FROM investigation.vw_prioritized_alerts
                    """
                )
            ).mappings().one()

            source_count = connection.execute(
                text("SELECT COUNT(*) FROM risk.alerts")
            ).scalar_one()

            checks["source_reconciliation"] = (
                summary["total"] == source_count
            )

            checks["unique_alert_ids"] = (
                summary["unique_alerts"] == source_count
            )

            checks["score_range"] = (
                summary["invalid_scores"] == 0
                and summary["missing_scores"] == 0
            )

            checks["valid_priority_tiers"] = (
                summary["invalid_tiers"] == 0
            )

            checks["score_components"] = (
                summary["component_mismatches"] == 0
            )

            checks["tier_thresholds"] = (
                summary["tier_mismatches"] == 0
            )

            view_columns = {
                row[0]
                for row in connection.execute(
                    text(
                        """
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_schema = 'investigation'
                          AND table_name = 'vw_prioritized_alerts'
                        """
                    )
                )
            }

            checks["no_label_in_view"] = (
                "is_laundering" not in view_columns
            )

            distribution = connection.execute(
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
            ).mappings().all()

        print("\nPHASE 9 INVESTIGATION VALIDATION")
        print("=" * 45)

        for name, passed in checks.items():
            status = "PASS" if passed else "FAIL"
            print(f"{status}: {name}")

        print("\nPriority distribution:")

        for row in distribution:
            print(
                f"{row['priority_tier']}: "
                f"{row['alert_count']:,} alerts "
                f"(scores {row['minimum_score']}–"
                f"{row['maximum_score']})"
            )

        passed_count = sum(checks.values())

        print(
            f"\nValidation: "
            f"{passed_count}/{len(checks)} PASS"
        )

        if not all(checks.values()):
            raise SystemExit(
                "PHASE 9 VALIDATION FAILED"
            )

        print("PHASE 9 VALIDATION PASSED")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
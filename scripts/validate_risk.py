from sqlalchemy import create_engine, text

from src.common.config import get_settings

CHECKS = {
    "scored_transaction_count": (
        "SELECT COUNT(*) FROM risk.transaction_scores",
        5078345,
    ),
    "orphan_scores": (
        "SELECT COUNT(*) FROM risk.transaction_scores s "
        "LEFT JOIN warehouse.fact_transactions f "
        "ON f.transaction_id = s.transaction_id "
        "WHERE f.transaction_id IS NULL",
        0,
    ),
    "invalid_score_ranges": (
        "SELECT COUNT(*) FROM risk.transaction_scores "
        "WHERE risk_score < 0 OR risk_score > 100",
        0,
    ),
    "invalid_risk_levels": (
        "SELECT COUNT(*) FROM risk.transaction_scores "
        "WHERE (risk_score >= 80 AND risk_level <> 'CRITICAL') "
        "OR (risk_score >= 50 AND risk_score < 80 "
        "AND risk_level <> 'HIGH') "
        "OR (risk_score >= 25 AND risk_score < 50 "
        "AND risk_level <> 'MEDIUM') "
        "OR (risk_score < 25 AND risk_level <> 'LOW')",
        0,
    ),
    "rule_hit_count_mismatches": (
        "SELECT COUNT(*) FROM risk.transaction_scores s "
        "LEFT JOIN ("
        "SELECT transaction_id, COUNT(*) AS hits "
        "FROM risk.rule_hits GROUP BY transaction_id"
        ") h ON h.transaction_id = s.transaction_id "
        "WHERE s.triggered_rule_count <> COALESCE(h.hits, 0)",
        0,
    ),
    "missing_high_risk_alerts": (
        "SELECT COUNT(*) FROM risk.transaction_scores s "
        "LEFT JOIN risk.alerts a "
        "ON a.transaction_id = s.transaction_id "
        "WHERE s.risk_level IN ('HIGH', 'CRITICAL') "
        "AND a.transaction_id IS NULL",
        0,
    ),
    "unexpected_low_risk_alerts": (
        "SELECT COUNT(*) FROM risk.alerts a "
        "JOIN risk.transaction_scores s "
        "ON s.transaction_id = a.transaction_id "
        "WHERE s.risk_level NOT IN ('HIGH', 'CRITICAL')",
        0,
    ),
    "alert_score_mismatches": (
        "SELECT COUNT(*) FROM risk.alerts a "
        "JOIN risk.transaction_scores s "
        "ON s.transaction_id = a.transaction_id "
        "WHERE a.risk_score <> s.risk_score "
        "OR a.risk_level <> s.risk_level",
        0,
    ),
}


def main() -> None:
    engine = create_engine(get_settings().database_url)
    failures = []

    try:
        with engine.connect() as connection:
            for name, (query, expected) in CHECKS.items():
                actual = connection.execute(text(query)).scalar_one()
                status = "PASS" if actual == expected else "FAIL"
                print(f"{status}: {name} = {actual:,}", flush=True)
                if actual != expected:
                    failures.append(name)

            print("\nRISK LEVEL DISTRIBUTION:")
            levels = connection.execute(
                text(
                    "SELECT risk_level, COUNT(*) "
                    "FROM risk.transaction_scores "
                    "GROUP BY risk_level ORDER BY risk_level"
                )
            ).all()
            for level, count in levels:
                print(f"{level}: {count:,}")

            print("\nRULE HIT DISTRIBUTION:")
            rules = connection.execute(
                text(
                    "SELECT rule_code, COUNT(*) "
                    "FROM risk.rule_hits "
                    "GROUP BY rule_code ORDER BY rule_code"
                )
            ).all()
            for rule, count in rules:
                print(f"{rule}: {count:,}")

            alert_count = connection.execute(
                text("SELECT COUNT(*) FROM risk.alerts")
            ).scalar_one()
            print(f"\nTOTAL ALERTS: {alert_count:,}")
    finally:
        engine.dispose()

    if failures:
        raise SystemExit(f"PHASE 6 VALIDATION FAILED: {failures}")

    print("\nPHASE 6 RISK VALIDATION PASSED")


if __name__ == "__main__":
    main()

import time

from sqlalchemy import create_engine, text

from src.common.config import get_settings

BATCH_SIZE = 100_000

SCORE_SQL = """
WITH candidates AS (
    SELECT
        f.transaction_id,
        (
            CASE WHEN f.amount_paid >= t.p99_amount
                AND c1.is_active THEN c1.risk_points ELSE 0 END
            + CASE WHEN f.is_cross_currency
                AND c2.is_active THEN c2.risk_points ELSE 0 END
            + CASE WHEN se.bank_id <> re.bank_id
                AND c3.is_active THEN c3.risk_points ELSE 0 END
            + CASE WHEN f.is_duplicate_candidate
                AND c4.is_active THEN c4.risk_points ELSE 0 END
        ) AS points,
        (
            CASE WHEN f.amount_paid >= t.p99_amount
                AND c1.is_active THEN 1 ELSE 0 END
            + CASE WHEN f.is_cross_currency
                AND c2.is_active THEN 1 ELSE 0 END
            + CASE WHEN se.bank_id <> re.bank_id
                AND c3.is_active THEN 1 ELSE 0 END
            + CASE WHEN f.is_duplicate_candidate
                AND c4.is_active THEN 1 ELSE 0 END
        ) AS hit_count
    FROM warehouse.fact_transactions f
    JOIN risk.currency_thresholds t
        ON t.currency_key = f.payment_currency_key
    JOIN warehouse.dim_entity se
        ON se.entity_key = f.sender_entity_key
    JOIN warehouse.dim_entity re
        ON re.entity_key = f.receiver_entity_key
    CROSS JOIN risk.rule_catalog c1
    CROSS JOIN risk.rule_catalog c2
    CROSS JOIN risk.rule_catalog c3
    CROSS JOIN risk.rule_catalog c4
    WHERE c1.rule_code = 'HIGH_VALUE'
      AND c2.rule_code = 'CROSS_CURRENCY'
      AND c3.rule_code = 'CROSS_BANK'
      AND c4.rule_code = 'DUPLICATE'
      AND f.transaction_id > :low
      AND f.transaction_id <= :high
)
INSERT INTO risk.transaction_scores (
    transaction_id, risk_score, risk_level,
    triggered_rule_count, scored_at
)
SELECT
    transaction_id,
    LEAST(points, 100)::SMALLINT,
    CASE
        WHEN points >= 80 THEN 'CRITICAL'
        WHEN points >= 50 THEN 'HIGH'
        WHEN points >= 25 THEN 'MEDIUM'
        ELSE 'LOW'
    END,
    hit_count::SMALLINT,
    NOW()
FROM candidates
ON CONFLICT (transaction_id) DO UPDATE SET
    risk_score = EXCLUDED.risk_score,
    risk_level = EXCLUDED.risk_level,
    triggered_rule_count = EXCLUDED.triggered_rule_count,
    scored_at = NOW()
"""

HITS_SQL = """
INSERT INTO risk.rule_hits (transaction_id, rule_code)
SELECT f.transaction_id, 'HIGH_VALUE'
FROM warehouse.fact_transactions f
JOIN risk.currency_thresholds t
    ON t.currency_key = f.payment_currency_key
JOIN risk.rule_catalog r ON r.rule_code = 'HIGH_VALUE'
WHERE f.transaction_id > :low AND f.transaction_id <= :high
  AND f.amount_paid >= t.p99_amount AND r.is_active
UNION ALL
SELECT f.transaction_id, 'CROSS_CURRENCY'
FROM warehouse.fact_transactions f
JOIN risk.rule_catalog r ON r.rule_code = 'CROSS_CURRENCY'
WHERE f.transaction_id > :low AND f.transaction_id <= :high
  AND f.is_cross_currency AND r.is_active
UNION ALL
SELECT f.transaction_id, 'CROSS_BANK'
FROM warehouse.fact_transactions f
JOIN warehouse.dim_entity se
    ON se.entity_key = f.sender_entity_key
JOIN warehouse.dim_entity re
    ON re.entity_key = f.receiver_entity_key
JOIN risk.rule_catalog r ON r.rule_code = 'CROSS_BANK'
WHERE f.transaction_id > :low AND f.transaction_id <= :high
  AND se.bank_id <> re.bank_id AND r.is_active
UNION ALL
SELECT f.transaction_id, 'DUPLICATE'
FROM warehouse.fact_transactions f
JOIN risk.rule_catalog r ON r.rule_code = 'DUPLICATE'
WHERE f.transaction_id > :low AND f.transaction_id <= :high
  AND f.is_duplicate_candidate AND r.is_active
ON CONFLICT (transaction_id, rule_code) DO NOTHING
"""

ALERT_SQL = """
INSERT INTO risk.alerts (
    transaction_id, risk_score, risk_level
)
SELECT transaction_id, risk_score, risk_level
FROM risk.transaction_scores
WHERE transaction_id > :low AND transaction_id <= :high
  AND risk_level IN ('HIGH', 'CRITICAL')
ON CONFLICT (transaction_id) DO UPDATE SET
    risk_score = EXCLUDED.risk_score,
    risk_level = EXCLUDED.risk_level
"""


def build_risk_scores(
    database_url: str,
    batch_size: int = BATCH_SIZE,
) -> dict:
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    engine = create_engine(database_url, pool_pre_ping=True)
    started = time.monotonic()

    try:
        with engine.connect() as connection:
            source_rows = connection.execute(
                text("SELECT COUNT(*) FROM warehouse.fact_transactions")
            ).scalar_one()
            completed = connection.execute(
                text("SELECT COUNT(*) FROM risk.transaction_scores")
            ).scalar_one()
            last_id = connection.execute(
                text(
                    "SELECT COALESCE(MAX(transaction_id), 0) "
                    "FROM risk.transaction_scores"
                )
            ).scalar_one()

        print(
            f"Resuming risk scoring: {completed:,}/{source_rows:,}",
            flush=True,
        )

        while completed < source_rows:
            with engine.begin() as connection:
                upper = connection.execute(
                    text(
                        "SELECT transaction_id "
                        "FROM warehouse.fact_transactions "
                        "WHERE transaction_id > :last_id "
                        "ORDER BY transaction_id "
                        "LIMIT 1 OFFSET :offset"
                    ),
                    {"last_id": last_id, "offset": batch_size - 1},
                ).scalar_one_or_none()

                if upper is None:
                    upper = connection.execute(
                        text(
                            "SELECT MAX(transaction_id) "
                            "FROM warehouse.fact_transactions "
                            "WHERE transaction_id > :last_id"
                        ),
                        {"last_id": last_id},
                    ).scalar_one_or_none()

                if upper is None:
                    break

                params = {"low": last_id, "high": upper}
                connection.execute(text(SCORE_SQL), params)
                connection.execute(text(HITS_SQL), params)
                connection.execute(text(ALERT_SQL), params)

            last_id = upper

            with engine.connect() as connection:
                completed = connection.execute(
                    text(
                        "SELECT COUNT(*) FROM risk.transaction_scores"
                    )
                ).scalar_one()

            elapsed = max(time.monotonic() - started, 0.001)
            remaining = max(source_rows - completed, 0)
            processed = max(completed, 1)
            eta = remaining * elapsed / processed / 60

            print(
                f"Progress: {completed / source_rows * 100:6.2f}% "
                f"| Done: {completed:,} "
                f"| Left: {remaining:,} "
                f"| ETA estimate: {eta:.1f} min",
                flush=True,
            )

        with engine.connect() as connection:
            scored = connection.execute(
                text("SELECT COUNT(*) FROM risk.transaction_scores")
            ).scalar_one()
            alerts = connection.execute(
                text("SELECT COUNT(*) FROM risk.alerts")
            ).scalar_one()

        if scored != source_rows:
            raise RuntimeError(
                f"Risk reconciliation failed: "
                f"source={source_rows}, scored={scored}"
            )

        result = {
            "status": "completed",
            "source_rows": source_rows,
            "scored_rows": scored,
            "alerts": alerts,
        }
        print(f"Phase 6 risk scoring completed: {result}", flush=True)
        return result
    finally:
        engine.dispose()


if __name__ == "__main__":
    build_risk_scores(get_settings().database_url)

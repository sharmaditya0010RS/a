import time
from pathlib import Path

from sqlalchemy import create_engine, text

from src.common.config import get_settings

ROOT = Path("sql/behavior")
ROOT.mkdir(parents=True, exist_ok=True)

(ROOT / "008_create_advanced_profiles.sql").write_text(
    """
CREATE TABLE IF NOT EXISTS behavior.entity_daily_advanced (
    entity_key TEXT NOT NULL REFERENCES warehouse.dim_entity(entity_key),
    date_key INTEGER NOT NULL REFERENCES warehouse.dim_date(date_key),
    rapid_movement_count BIGINT NOT NULL DEFAULT 0,
    structuring_candidate_count BIGINT NOT NULL DEFAULT 0,
    structuring_amount NUMERIC NOT NULL DEFAULT 0,
    refreshed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (entity_key, date_key)
);

CREATE TABLE IF NOT EXISTS behavior.entity_risk_profiles (
    entity_key TEXT PRIMARY KEY REFERENCES warehouse.dim_entity(entity_key),
    active_days BIGINT NOT NULL,
    outgoing_transactions BIGINT NOT NULL,
    incoming_transactions BIGINT NOT NULL,
    velocity_days BIGINT NOT NULL,
    fan_in_days BIGINT NOT NULL,
    fan_out_days BIGINT NOT NULL,
    high_behavior_days BIGINT NOT NULL,
    rapid_movement_count BIGINT NOT NULL,
    structuring_candidate_days BIGINT NOT NULL,
    max_behavior_score SMALLINT NOT NULL,
    entity_risk_score SMALLINT NOT NULL
        CHECK (entity_risk_score BETWEEN 0 AND 100),
    entity_risk_level TEXT NOT NULL
        CHECK (entity_risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    refreshed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_entity_profiles_level
ON behavior.entity_risk_profiles(entity_risk_level);

CREATE INDEX IF NOT EXISTS ix_entity_advanced_date
ON behavior.entity_daily_advanced(date_key);
""",
    encoding="utf-8",
)

(ROOT / "009_build_advanced_daily.sql").write_text(
    """
WITH rapid AS (
    SELECT
        r.entity_key,
        o.date_key,
        COUNT(*) AS rapid_count
    FROM behavior.rapid_movement r
    JOIN warehouse.fact_transactions o
      ON o.transaction_id = r.outgoing_transaction_id
    WHERE o.date_key = :date_key
    GROUP BY r.entity_key, o.date_key
),
structuring AS (
    SELECT
        f.sender_entity_key AS entity_key,
        f.date_key,
        f.payment_currency_key,
        COUNT(*) AS tx_count,
        SUM(f.amount_paid) AS total_amount
    FROM warehouse.fact_transactions f
    JOIN risk.currency_thresholds t
      ON t.currency_key = f.payment_currency_key
    WHERE f.date_key = :date_key
      AND f.amount_paid > 0
      AND f.amount_paid < t.p99_amount
    GROUP BY
        f.sender_entity_key,
        f.date_key,
        f.payment_currency_key,
    HAVING COUNT(*) >= 3
       AND SUM(f.amount_paid) >= MAX(t.p99_amount)
),
structuring_by_entity AS (
    SELECT
        entity_key,
        date_key,
        SUM(tx_count) AS candidate_count,
        SUM(total_amount) AS candidate_amount
    FROM structuring
    GROUP BY entity_key, date_key
)
INSERT INTO behavior.entity_daily_advanced (
    entity_key,
    date_key,
    rapid_movement_count,
    structuring_candidate_count,
    structuring_amount,
    refreshed_at
)
SELECT
    a.entity_key,
    a.date_key,
    COALESCE(r.rapid_count, 0),
    COALESCE(s.candidate_count, 0),
    COALESCE(s.candidate_amount, 0),
    NOW()
FROM behavior.entity_daily_activity a
LEFT JOIN rapid r
  ON r.entity_key = a.entity_key
 AND r.date_key = a.date_key
LEFT JOIN structuring_by_entity s
  ON s.entity_key = a.entity_key
 AND s.date_key = a.date_key
WHERE a.date_key = :date_key
ON CONFLICT (entity_key, date_key) DO UPDATE SET
    rapid_movement_count = EXCLUDED.rapid_movement_count,
    structuring_candidate_count = EXCLUDED.structuring_candidate_count,
    structuring_amount = EXCLUDED.structuring_amount,
    refreshed_at = NOW();
""".replace(
    "f.payment_currency_key,\n    HAVING",
    "f.payment_currency_key\n    HAVING",
),
    encoding="utf-8",
)

(ROOT / "010_build_entity_profiles.sql").write_text(
    """
WITH aggregated AS (
    SELECT
        s.entity_key,
        COUNT(*) AS active_days,
        SUM(s.outgoing_count) AS outgoing_transactions,
        SUM(s.incoming_count) AS incoming_transactions,
        COUNT(*) FILTER (WHERE s.velocity_flag) AS velocity_days,
        COUNT(*) FILTER (WHERE s.fan_in_flag) AS fan_in_days,
        COUNT(*) FILTER (WHERE s.fan_out_flag) AS fan_out_days,
        COUNT(*) FILTER (
            WHERE s.behavior_level IN ('HIGH', 'CRITICAL')
        ) AS high_behavior_days,
        SUM(a.rapid_movement_count) AS rapid_movement_count,
        COUNT(*) FILTER (
            WHERE a.structuring_candidate_count > 0
        ) AS structuring_candidate_days,
        MAX(s.behavior_score) AS max_behavior_score
    FROM behavior.entity_daily_signals s
    JOIN behavior.entity_daily_advanced a
      ON a.entity_key = s.entity_key
     AND a.date_key = s.date_key
    GROUP BY s.entity_key
),
scored AS (
    SELECT *,
        LEAST(
            100,
            max_behavior_score
            + CASE
                WHEN rapid_movement_count >= 5 THEN 15
                WHEN rapid_movement_count >= 1 THEN 5
                ELSE 0
              END
            + CASE
                WHEN structuring_candidate_days >= 2 THEN 20
                WHEN structuring_candidate_days >= 1 THEN 10
                ELSE 0
              END
        )::SMALLINT AS final_score
    FROM aggregated
)
INSERT INTO behavior.entity_risk_profiles (
    entity_key,
    active_days,
    outgoing_transactions,
    incoming_transactions,
    velocity_days,
    fan_in_days,
    fan_out_days,
    high_behavior_days,
    rapid_movement_count,
    structuring_candidate_days,
    max_behavior_score,
    entity_risk_score,
    entity_risk_level,
    refreshed_at
)
SELECT
    entity_key,
    active_days,
    outgoing_transactions,
    incoming_transactions,
    velocity_days,
    fan_in_days,
    fan_out_days,
    high_behavior_days,
    rapid_movement_count,
    structuring_candidate_days,
    max_behavior_score,
    final_score,
    CASE
        WHEN final_score >= 80 THEN 'CRITICAL'
        WHEN final_score >= 50 THEN 'HIGH'
        WHEN final_score >= 25 THEN 'MEDIUM'
        ELSE 'LOW'
    END,
    NOW()
FROM scored
ON CONFLICT (entity_key) DO UPDATE SET
    active_days = EXCLUDED.active_days,
    outgoing_transactions = EXCLUDED.outgoing_transactions,
    incoming_transactions = EXCLUDED.incoming_transactions,
    velocity_days = EXCLUDED.velocity_days,
    fan_in_days = EXCLUDED.fan_in_days,
    fan_out_days = EXCLUDED.fan_out_days,
    high_behavior_days = EXCLUDED.high_behavior_days,
    rapid_movement_count = EXCLUDED.rapid_movement_count,
    structuring_candidate_days = EXCLUDED.structuring_candidate_days,
    max_behavior_score = EXCLUDED.max_behavior_score,
    entity_risk_score = EXCLUDED.entity_risk_score,
    entity_risk_level = EXCLUDED.entity_risk_level,
    refreshed_at = NOW();
""",
    encoding="utf-8",
)

engine = create_engine(
    get_settings().database_url,
    pool_pre_ping=True,
)

try:
    with engine.begin() as connection:
        connection.exec_driver_sql(
            (ROOT / "008_create_advanced_profiles.sql").read_text(
                encoding="utf-8"
            )
        )

    with engine.connect() as connection:
        dates = connection.execute(
            text(
                "SELECT DISTINCT date_key "
                "FROM behavior.entity_daily_activity "
                "ORDER BY date_key"
            )
        ).scalars().all()

    daily_sql = text(
        (ROOT / "009_build_advanced_daily.sql").read_text(
            encoding="utf-8"
        )
    )

    print("Building advanced behavioural indicators...", flush=True)

    for index, date_key in enumerate(dates, start=1):
        started = time.monotonic()

        with engine.begin() as connection:
            connection.execute(daily_sql, {"date_key": date_key})

        print(
            f"[{index}/{len(dates)}] "
            f"date_key={date_key} "
            f"elapsed={time.monotonic() - started:.1f}s",
            flush=True,
        )

    print("Building consolidated entity risk profiles...", flush=True)

    with engine.begin() as connection:
        connection.execute(
            text(
                (ROOT / "010_build_entity_profiles.sql").read_text(
                    encoding="utf-8"
                )
            )
        )

    with engine.connect() as connection:
        checks = {
            "daily_reconciliation": """
                SELECT (
                    (SELECT COUNT(*) FROM behavior.entity_daily_activity)
                    -
                    (SELECT COUNT(*) FROM behavior.entity_daily_advanced)
                )
            """,
            "missing_daily_records": """
                SELECT COUNT(*)
                FROM behavior.entity_daily_activity a
                LEFT JOIN behavior.entity_daily_advanced d
                  ON a.entity_key = d.entity_key
                 AND a.date_key = d.date_key
                WHERE d.entity_key IS NULL
            """,
            "orphan_daily_records": """
                SELECT COUNT(*)
                FROM behavior.entity_daily_advanced d
                LEFT JOIN behavior.entity_daily_activity a
                  ON a.entity_key = d.entity_key
                 AND a.date_key = d.date_key
                WHERE a.entity_key IS NULL
            """,
            "invalid_rapid_movement_windows": """
                SELECT COUNT(*)
                FROM behavior.rapid_movement
                WHERE minutes_between < 0
                   OR minutes_between > 60
                   OR incoming_transaction_id = outgoing_transaction_id
            """,
            "invalid_entity_risk_levels": """
                SELECT COUNT(*)
                FROM behavior.entity_risk_profiles
                WHERE entity_risk_level <> CASE
                    WHEN entity_risk_score >= 80 THEN 'CRITICAL'
                    WHEN entity_risk_score >= 50 THEN 'HIGH'
                    WHEN entity_risk_score >= 25 THEN 'MEDIUM'
                    ELSE 'LOW'
                END
            """,
            "missing_entity_profiles": """
                SELECT COUNT(*)
                FROM warehouse.dim_entity e
                WHERE EXISTS (
                    SELECT 1
                    FROM behavior.entity_daily_activity a
                    WHERE a.entity_key = e.entity_key
                )
                AND NOT EXISTS (
                    SELECT 1
                    FROM behavior.entity_risk_profiles p
                    WHERE p.entity_key = e.entity_key
                )
            """,
            "rapid_count_reconciliation": """
                SELECT ABS(
                    (SELECT COUNT(*) FROM behavior.rapid_movement)
                    -
                    (SELECT COALESCE(SUM(rapid_movement_count), 0)
                     FROM behavior.entity_daily_advanced)
                )
            """,
        }

        failures = []

        for name, query in checks.items():
            result = connection.execute(text(query)).scalar_one()
            status = "PASS" if result == 0 else "FAIL"
            print(f"{status}: {name} = {result:,}", flush=True)
            if result != 0:
                failures.append(name)

        print("\nENTITY RISK DISTRIBUTION:", flush=True)

        for level, count in connection.execute(
            text(
                "SELECT entity_risk_level, COUNT(*) "
                "FROM behavior.entity_risk_profiles "
                "GROUP BY entity_risk_level "
                "ORDER BY entity_risk_level"
            )
        ):
            print(f"{level}: {count:,}", flush=True)

        totals = connection.execute(
            text(
                "SELECT "
                "COUNT(*), "
                "COALESCE(SUM(structuring_candidate_days), 0) "
                "FROM behavior.entity_risk_profiles"
            )
        ).one()

        print(f"\nEntity profiles: {totals[0]:,}", flush=True)
        print(
            f"Structuring candidate entity-days: {totals[1]:,}",
            flush=True,
        )

        if failures:
            raise RuntimeError(f"Validation failed: {failures}")

    print("\nPHASE 7 ADVANCED INTELLIGENCE PASSED", flush=True)

finally:
    engine.dispose()

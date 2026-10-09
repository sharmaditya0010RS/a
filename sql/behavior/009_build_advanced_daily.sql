
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
        f.payment_currency_key
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

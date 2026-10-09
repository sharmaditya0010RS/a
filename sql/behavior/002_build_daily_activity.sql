WITH outgoing AS (
    SELECT
        f.sender_entity_key AS entity_key,
        f.date_key,
        COUNT(*) AS outgoing_count,
        SUM(f.amount_paid) AS outgoing_amount,
        COUNT(DISTINCT f.receiver_entity_key) AS distinct_receivers,
        COUNT(*) FILTER (
            WHERE f.is_cross_currency
        ) AS cross_currency_outgoing,
        COUNT(*) FILTER (
            WHERE f.amount_paid >= t.p99_amount
        ) AS high_value_outgoing
    FROM warehouse.fact_transactions f
    JOIN risk.currency_thresholds t
        ON t.currency_key = f.payment_currency_key
    WHERE f.date_key = :date_key
    GROUP BY f.sender_entity_key, f.date_key
),
incoming AS (
    SELECT
        f.receiver_entity_key AS entity_key,
        f.date_key,
        COUNT(*) AS incoming_count,
        SUM(f.amount_received) AS incoming_amount,
        COUNT(DISTINCT f.sender_entity_key) AS distinct_senders
    FROM warehouse.fact_transactions f
    WHERE f.date_key = :date_key
    GROUP BY f.receiver_entity_key, f.date_key
)
INSERT INTO behavior.entity_daily_activity (
    entity_key,
    date_key,
    outgoing_count,
    incoming_count,
    outgoing_amount,
    incoming_amount,
    distinct_receivers,
    distinct_senders,
    cross_currency_outgoing,
    high_value_outgoing,
    refreshed_at
)
SELECT
    COALESCE(o.entity_key, i.entity_key),
    COALESCE(o.date_key, i.date_key),
    COALESCE(o.outgoing_count, 0),
    COALESCE(i.incoming_count, 0),
    COALESCE(o.outgoing_amount, 0),
    COALESCE(i.incoming_amount, 0),
    COALESCE(o.distinct_receivers, 0),
    COALESCE(i.distinct_senders, 0),
    COALESCE(o.cross_currency_outgoing, 0),
    COALESCE(o.high_value_outgoing, 0),
    NOW()
FROM outgoing o
FULL OUTER JOIN incoming i
    ON o.entity_key = i.entity_key
    AND o.date_key = i.date_key
ON CONFLICT (entity_key, date_key) DO UPDATE SET
    outgoing_count = EXCLUDED.outgoing_count,
    incoming_count = EXCLUDED.incoming_count,
    outgoing_amount = EXCLUDED.outgoing_amount,
    incoming_amount = EXCLUDED.incoming_amount,
    distinct_receivers = EXCLUDED.distinct_receivers,
    distinct_senders = EXCLUDED.distinct_senders,
    cross_currency_outgoing = EXCLUDED.cross_currency_outgoing,
    high_value_outgoing = EXCLUDED.high_value_outgoing,
    refreshed_at = NOW();

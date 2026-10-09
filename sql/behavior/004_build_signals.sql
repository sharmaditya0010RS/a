WITH scored AS (
    SELECT
        entity_key,
        date_key,
        outgoing_count,
        incoming_count,
        distinct_receivers,
        distinct_senders,
        outgoing_count >= 20 AS velocity_flag,
        distinct_senders >= 10 AS fan_in_flag,
        distinct_receivers >= 10 AS fan_out_flag,
        cross_currency_outgoing >= 5 AS cross_currency_flag,
        high_value_outgoing >= 3 AS high_value_flag,
        (
            CASE WHEN outgoing_count >= 20 THEN 30 ELSE 0 END
            + CASE WHEN distinct_senders >= 10 THEN 25 ELSE 0 END
            + CASE WHEN distinct_receivers >= 10 THEN 25 ELSE 0 END
            + CASE WHEN cross_currency_outgoing >= 5 THEN 10 ELSE 0 END
            + CASE WHEN high_value_outgoing >= 3 THEN 10 ELSE 0 END
        ) AS points
    FROM behavior.entity_daily_activity
    WHERE date_key = :date_key
)
INSERT INTO behavior.entity_daily_signals (
    entity_key,
    date_key,
    outgoing_count,
    incoming_count,
    distinct_receivers,
    distinct_senders,
    velocity_flag,
    fan_in_flag,
    fan_out_flag,
    cross_currency_flag,
    high_value_flag,
    behavior_score,
    behavior_level,
    scored_at
)
SELECT
    entity_key,
    date_key,
    outgoing_count,
    incoming_count,
    distinct_receivers,
    distinct_senders,
    velocity_flag,
    fan_in_flag,
    fan_out_flag,
    cross_currency_flag,
    high_value_flag,
    points::SMALLINT,
    CASE
        WHEN points >= 80 THEN 'CRITICAL'
        WHEN points >= 50 THEN 'HIGH'
        WHEN points >= 25 THEN 'MEDIUM'
        ELSE 'LOW'
    END,
    NOW()
FROM scored
ON CONFLICT (entity_key, date_key) DO UPDATE SET
    outgoing_count = EXCLUDED.outgoing_count,
    incoming_count = EXCLUDED.incoming_count,
    distinct_receivers = EXCLUDED.distinct_receivers,
    distinct_senders = EXCLUDED.distinct_senders,
    velocity_flag = EXCLUDED.velocity_flag,
    fan_in_flag = EXCLUDED.fan_in_flag,
    fan_out_flag = EXCLUDED.fan_out_flag,
    cross_currency_flag = EXCLUDED.cross_currency_flag,
    high_value_flag = EXCLUDED.high_value_flag,
    behavior_score = EXCLUDED.behavior_score,
    behavior_level = EXCLUDED.behavior_level,
    scored_at = NOW();

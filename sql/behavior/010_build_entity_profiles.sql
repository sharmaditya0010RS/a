
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

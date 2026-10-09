CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE VIEW analytics.vw_executive_kpis AS
WITH transaction_metrics AS (
    SELECT
        COUNT(*) AS total_transactions,
        COUNT(*) FILTER (
            WHERE is_laundering = 1
        ) AS aml_positive_transactions,
        COUNT(*) FILTER (
            WHERE is_cross_currency
        ) AS cross_currency_transactions,
        COUNT(*) FILTER (
            WHERE is_duplicate_candidate
        ) AS duplicate_candidates
    FROM warehouse.fact_transactions
),
alert_metrics AS (
    SELECT
        COUNT(*) AS total_alerts,
        COUNT(*) FILTER (
            WHERE alert_status = 'OPEN'
        ) AS open_alerts,
        COUNT(*) FILTER (
            WHERE risk_level = 'CRITICAL'
        ) AS critical_alerts
    FROM risk.alerts
),
entity_metrics AS (
    SELECT
        COUNT(*) AS total_entities,
        COUNT(*) FILTER (
            WHERE entity_risk_level IN ('HIGH', 'CRITICAL')
        ) AS high_risk_entities
    FROM behavior.entity_risk_profiles
)
SELECT
    t.*,
    a.*,
    e.*,
    ROUND(
        100.0 * a.total_alerts
        / NULLIF(t.total_transactions, 0),
        4
    ) AS alert_rate_pct
FROM transaction_metrics t
CROSS JOIN alert_metrics a
CROSS JOIN entity_metrics e;

CREATE OR REPLACE VIEW analytics.vw_investigation_queue AS
SELECT
    a.alert_id,
    a.transaction_id,
    a.risk_score,
    a.risk_level,
    a.alert_status,
    a.created_at,
    f.transaction_timestamp,
    f.date_key,
    f.sender_entity_key,
    f.receiver_entity_key,
    f.amount_paid,
    f.payment_currency_key,
    f.is_cross_currency,
    sp.entity_risk_score AS sender_entity_risk_score,
    sp.entity_risk_level AS sender_entity_risk_level,
    rp.entity_risk_score AS receiver_entity_risk_score,
    rp.entity_risk_level AS receiver_entity_risk_level,
    (
        SELECT STRING_AGG(h.rule_code, ', ' ORDER BY h.rule_code)
        FROM risk.rule_hits h
        WHERE h.transaction_id = a.transaction_id
    ) AS triggered_rules
FROM risk.alerts a
JOIN warehouse.fact_transactions f
    ON f.transaction_id = a.transaction_id
LEFT JOIN behavior.entity_risk_profiles sp
    ON sp.entity_key = f.sender_entity_key
LEFT JOIN behavior.entity_risk_profiles rp
    ON rp.entity_key = f.receiver_entity_key;

CREATE OR REPLACE VIEW analytics.vw_entity_risk_leaderboard AS
SELECT
    p.entity_key,
    e.bank_id,
    e.account_id,
    p.entity_risk_score,
    p.entity_risk_level,
    p.active_days,
    p.outgoing_transactions,
    p.incoming_transactions,
    p.velocity_days,
    p.fan_in_days,
    p.fan_out_days,
    p.high_behavior_days,
    p.rapid_movement_count,
    p.structuring_candidate_days
FROM behavior.entity_risk_profiles p
JOIN warehouse.dim_entity e
    ON e.entity_key = p.entity_key;

CREATE OR REPLACE VIEW analytics.vw_daily_risk_trends AS
SELECT
    d.full_date,
    m.transaction_count,
    m.aml_positive_count,
    m.cross_currency_count,
    m.duplicate_candidate_count,
    COALESCE(a.alert_count, 0) AS alert_count,
    COALESCE(a.high_alert_count, 0) AS high_alert_count,
    COALESCE(a.critical_alert_count, 0) AS critical_alert_count
FROM warehouse.mart_daily_aml m
JOIN warehouse.dim_date d
    ON d.date_key = m.date_key
LEFT JOIN (
    SELECT
        f.date_key,
        COUNT(*) AS alert_count,
        COUNT(*) FILTER (
            WHERE a.risk_level = 'HIGH'
        ) AS high_alert_count,
        COUNT(*) FILTER (
            WHERE a.risk_level = 'CRITICAL'
        ) AS critical_alert_count
    FROM risk.alerts a
    JOIN warehouse.fact_transactions f
        ON f.transaction_id = a.transaction_id
    GROUP BY f.date_key
) a
    ON a.date_key = m.date_key;

CREATE OR REPLACE VIEW analytics.vw_detection_effectiveness AS
WITH confusion AS (
    SELECT
        COUNT(*) FILTER (
            WHERE a.transaction_id IS NOT NULL
              AND f.is_laundering = 1
        ) AS true_positives,
        COUNT(*) FILTER (
            WHERE a.transaction_id IS NOT NULL
              AND f.is_laundering = 0
        ) AS false_positives,
        COUNT(*) FILTER (
            WHERE a.transaction_id IS NULL
              AND f.is_laundering = 1
        ) AS false_negatives,
        COUNT(*) FILTER (
            WHERE a.transaction_id IS NULL
              AND f.is_laundering = 0
        ) AS true_negatives
    FROM warehouse.fact_transactions f
    LEFT JOIN risk.alerts a
        ON a.transaction_id = f.transaction_id
)
SELECT
    *,
    ROUND(
        true_positives::NUMERIC
        / NULLIF(true_positives + false_positives, 0),
        6
    ) AS precision,
    ROUND(
        true_positives::NUMERIC
        / NULLIF(true_positives + false_negatives, 0),
        6
    ) AS recall,
    ROUND(
        2.0 * true_positives
        / NULLIF(
            2 * true_positives + false_positives + false_negatives,
            0
        ),
        6
    ) AS f1_score,
    ROUND(
        false_positives::NUMERIC
        / NULLIF(false_positives + true_negatives, 0),
        6
    ) AS false_positive_rate
FROM confusion;

CREATE SCHEMA IF NOT EXISTS investigation;

CREATE OR REPLACE VIEW
investigation.vw_prioritized_alerts
AS

WITH alert_context AS (

    SELECT
        a.alert_id,
        a.transaction_id,
        a.risk_score AS transaction_risk_score,
        a.risk_level AS transaction_risk_level,
        a.alert_status,
        a.created_at AS alert_created_at,

        f.transaction_timestamp,
        f.sender_entity_key,
        f.receiver_entity_key,
        f.amount_paid,
        f.payment_currency_key,
        f.is_cross_currency,

        COALESCE(
            sender.entity_risk_score,
            0
        ) AS sender_entity_risk_score,

        COALESCE(
            receiver.entity_risk_score,
            0
        ) AS receiver_entity_risk_score,

        COALESCE(
            sender.entity_risk_level,
            'UNKNOWN'
        ) AS sender_entity_risk_level,

        COALESCE(
            receiver.entity_risk_level,
            'UNKNOWN'
        ) AS receiver_entity_risk_level

    FROM risk.alerts AS a

    INNER JOIN warehouse.fact_transactions AS f
        ON f.transaction_id = a.transaction_id

    LEFT JOIN behavior.entity_risk_profiles AS sender
        ON sender.entity_key = f.sender_entity_key

    LEFT JOIN behavior.entity_risk_profiles AS receiver
        ON receiver.entity_key = f.receiver_entity_key

),

score_components AS (

    SELECT
        *,

        ROUND(
            LEAST(
                GREATEST(
                    transaction_risk_score::NUMERIC,
                    0
                ),
                100
            ) * 0.60
        )::INTEGER AS transaction_component,

        ROUND(
            LEAST(
                GREATEST(
                    GREATEST(
                        sender_entity_risk_score,
                        receiver_entity_risk_score
                    )::NUMERIC,
                    0
                ),
                100
            ) * 0.30
        )::INTEGER AS entity_component,

        CASE
            WHEN sender_entity_risk_level IN (
                'HIGH',
                'CRITICAL'
            )
            AND receiver_entity_risk_level IN (
                'HIGH',
                'CRITICAL'
            )
            THEN 10
            ELSE 0
        END AS dual_high_risk_component

    FROM alert_context

),

priority_scores AS (

    SELECT
        *,

        LEAST(
            100,
            transaction_component
            + entity_component
            + dual_high_risk_component
        ) AS investigation_priority_score

    FROM score_components

)

SELECT
    alert_id,
    transaction_id,
    transaction_risk_score,
    transaction_risk_level,
    alert_status,
    alert_created_at,

    transaction_timestamp,
    sender_entity_key,
    receiver_entity_key,
    amount_paid,
    payment_currency_key,
    is_cross_currency,

    sender_entity_risk_score,
    receiver_entity_risk_score,
    sender_entity_risk_level,
    receiver_entity_risk_level,

    transaction_component,
    entity_component,
    dual_high_risk_component,

    investigation_priority_score,

    CASE
        WHEN investigation_priority_score >= 80
            THEN 'P1'
        WHEN investigation_priority_score >= 65
            THEN 'P2'
        WHEN investigation_priority_score >= 50
            THEN 'P3'
        ELSE 'P4'
    END AS priority_tier

FROM priority_scores;
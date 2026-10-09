from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

from src.common.config import get_settings


@st.cache_resource
def investigation_engine():
    return create_engine(
        get_settings().database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
    )


def read_sql(
    sql: str,
    params: dict[str, Any] | None = None,
) -> pd.DataFrame:
    with investigation_engine().connect() as connection:
        return pd.read_sql_query(
            text(sql),
            connection,
            params=params or {},
        )


@st.cache_data(ttl=120, show_spinner=False)
def priority_summary() -> pd.DataFrame:
    return read_sql(
        """
        SELECT
            priority_tier,
            COUNT(*)::BIGINT AS alert_count,
            ROUND(
                AVG(investigation_priority_score),
                1
            ) AS average_priority_score
        FROM investigation.vw_prioritized_alerts
        GROUP BY priority_tier
        ORDER BY priority_tier
        """
    )


@st.cache_data(ttl=120, show_spinner=False)
def queue_count(
    tier: str,
    status: str,
    search_id: str,
) -> int:
    result = read_sql(
        """
        SELECT COUNT(*)::BIGINT AS total
        FROM investigation.vw_prioritized_alerts
        WHERE
            (:tier = 'ALL' OR priority_tier = :tier)
            AND (
                :status = 'ALL'
                OR alert_status = :status
            )
            AND (
                :search_id = ''
                OR alert_id::TEXT = :search_id
                OR transaction_id::TEXT = :search_id
            )
        """,
        {
            "tier": tier,
            "status": status,
            "search_id": search_id,
        },
    )

    return int(result.iloc[0]["total"])


@st.cache_data(ttl=120, show_spinner=False)
def investigation_queue(
    tier: str,
    status: str,
    search_id: str,
    limit: int,
    offset: int,
) -> pd.DataFrame:
    return read_sql(
        """
        SELECT
            alert_id,
            transaction_id,
            priority_tier,
            investigation_priority_score,
            transaction_risk_score,
            transaction_risk_level,
            alert_status,
            transaction_timestamp,
            sender_entity_key,
            receiver_entity_key,
            amount_paid,
            payment_currency_key
        FROM investigation.vw_prioritized_alerts
        WHERE
            (:tier = 'ALL' OR priority_tier = :tier)
            AND (
                :status = 'ALL'
                OR alert_status = :status
            )
            AND (
                :search_id = ''
                OR alert_id::TEXT = :search_id
                OR transaction_id::TEXT = :search_id
            )
        ORDER BY
            investigation_priority_score DESC,
            transaction_risk_score DESC,
            alert_id ASC
        LIMIT :limit
        OFFSET :offset
        """,
        {
            "tier": tier,
            "status": status,
            "search_id": search_id,
            "limit": limit,
            "offset": offset,
        },
    )


@st.cache_data(ttl=120, show_spinner=False)
def alert_evidence(alert_id: int) -> pd.DataFrame:
    return read_sql(
        """
        SELECT *
        FROM investigation.vw_prioritized_alerts
        WHERE alert_id = :alert_id
        """,
        {"alert_id": alert_id},
    )


@st.cache_data(ttl=120, show_spinner=False)
def triggered_rules(transaction_id: int) -> pd.DataFrame:
    return read_sql(
        """
        SELECT
            rule_code,
            detected_at
        FROM risk.rule_hits
        WHERE transaction_id = :transaction_id
        ORDER BY rule_code
        """,
        {"transaction_id": transaction_id},
    )


@st.cache_data(ttl=120, show_spinner=False)
def related_transactions(
    entity_key: str,
    limit: int = 100,
) -> pd.DataFrame:
    return read_sql(
        """
        SELECT
            transaction_id,
            transaction_timestamp,
            sender_entity_key,
            receiver_entity_key,
            amount_paid,
            payment_currency_key,
            is_cross_currency
        FROM warehouse.fact_transactions
        WHERE
            sender_entity_key = :entity_key
            OR receiver_entity_key = :entity_key
        ORDER BY
            transaction_timestamp DESC,
            transaction_id DESC
        LIMIT :limit
        """,
        {
            "entity_key": entity_key,
            "limit": limit,
        },
    )


@st.cache_data(ttl=120, show_spinner=False)
def counterparty_network(
    entity_key: str,
    limit: int = 12,
) -> pd.DataFrame:
    return read_sql(
        """
        WITH relationships AS (
            SELECT
                CASE
                    WHEN sender_entity_key = :entity_key
                        THEN receiver_entity_key
                    ELSE sender_entity_key
                END AS counterparty_key,

                CASE
                    WHEN sender_entity_key = :entity_key
                        THEN 'OUTGOING'
                    ELSE 'INCOMING'
                END AS direction

            FROM warehouse.fact_transactions

            WHERE
                sender_entity_key = :entity_key
                OR receiver_entity_key = :entity_key
        )

        SELECT
            counterparty_key,
            COUNT(*)::BIGINT AS transaction_count,
            COUNT(*) FILTER (
                WHERE direction = 'OUTGOING'
            )::BIGINT AS outgoing_count,
            COUNT(*) FILTER (
                WHERE direction = 'INCOMING'
            )::BIGINT AS incoming_count

        FROM relationships
        WHERE counterparty_key IS NOT NULL
        GROUP BY counterparty_key
        ORDER BY
            transaction_count DESC,
            counterparty_key ASC
        LIMIT :limit
        """,
        {
            "entity_key": entity_key,
            "limit": limit,
        },
    )


@st.cache_data(ttl=120, show_spinner=False)
def entity_profile(entity_key: str) -> pd.DataFrame:
    return read_sql(
        """
        SELECT
            entity_key,
            entity_risk_score,
            entity_risk_level,
            active_days,
            outgoing_transactions,
            incoming_transactions,
            velocity_days,
            fan_in_days,
            fan_out_days,
            high_behavior_days,
            rapid_movement_count,
            structuring_candidate_days
        FROM behavior.entity_risk_profiles
        WHERE entity_key = :entity_key
        """,
        {"entity_key": entity_key},
    )
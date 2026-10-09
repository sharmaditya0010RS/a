import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

from src.common.config import get_settings


@st.cache_resource
def get_engine():
    return create_engine(
        get_settings().database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
        pool_recycle=1800,
    )


@st.cache_data(ttl=180, show_spinner=False)
def query(
    sql: str,
    params: dict | None = None,
) -> pd.DataFrame:
    with get_engine().connect() as connection:
        return pd.read_sql_query(
            text(sql),
            connection,
            params=params or {},
        )


def health_check() -> bool:
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def executive_kpis():
    return query(
        "SELECT * FROM analytics.vw_executive_kpis"
    )


def daily_trends():
    return query(
        """
        SELECT *
        FROM analytics.vw_daily_risk_trends
        ORDER BY full_date
        """
    )


def risk_distribution():
    return query(
        """
        SELECT
            entity_risk_level AS risk_level,
            COUNT(*) AS entity_count
        FROM behavior.entity_risk_profiles
        GROUP BY entity_risk_level
        ORDER BY entity_count DESC
        """
    )


def alert_status_distribution():
    return query(
        """
        SELECT
            alert_status,
            COUNT(*) AS alert_count
        FROM risk.alerts
        GROUP BY alert_status
        ORDER BY alert_count DESC
        """
    )


def rule_distribution():
    return query(
        """
        SELECT
            rule_code,
            COUNT(*) AS triggered_transactions
        FROM risk.rule_hits
        GROUP BY rule_code
        ORDER BY triggered_transactions DESC
        """
    )


def alert_count(
    level: str,
    status: str,
    search: str,
) -> int:
    df = query(
        """
        SELECT COUNT(*) AS n
        FROM risk.alerts
        WHERE (:level = 'ALL' OR risk_level = :level)
          AND (:status = 'ALL' OR alert_status = :status)
          AND (
              :search = ''
              OR CAST(alert_id AS TEXT) = :search
              OR CAST(transaction_id AS TEXT) = :search
          )
        """,
        {
            "level": level,
            "status": status,
            "search": search,
        },
    )

    return int(df.iloc[0]["n"])


def alert_page(
    level: str,
    status: str,
    search: str,
    page: int,
    page_size: int,
):
    return query(
        """
        SELECT
            a.alert_id,
            a.transaction_id,
            a.risk_score,
            a.risk_level,
            a.alert_status,
            f.transaction_timestamp,
            f.sender_entity_key,
            f.receiver_entity_key,
            f.amount_paid,
            f.payment_currency_key
        FROM risk.alerts a
        JOIN warehouse.fact_transactions f
          ON f.transaction_id = a.transaction_id
        WHERE (:level = 'ALL' OR a.risk_level = :level)
          AND (:status = 'ALL' OR a.alert_status = :status)
          AND (
              :search = ''
              OR CAST(a.alert_id AS TEXT) = :search
              OR CAST(a.transaction_id AS TEXT) = :search
          )
        ORDER BY a.risk_score DESC, a.alert_id
        LIMIT :limit OFFSET :offset
        """,
        {
            "level": level,
            "status": status,
            "search": search,
            "limit": page_size,
            "offset": (page - 1) * page_size,
        },
    )


def alert_detail(alert_id: int):
    return query(
        """
        SELECT *
        FROM analytics.vw_investigation_queue
        WHERE alert_id = :alert_id
        """,
        {"alert_id": alert_id},
    )


def alert_rule_hits(transaction_id: int):
    return query(
        """
        SELECT
            h.rule_code,
            COUNT(*) AS hit_count
        FROM risk.rule_hits h
        WHERE h.transaction_id = :transaction_id
        GROUP BY h.rule_code
        ORDER BY h.rule_code
        """,
        {"transaction_id": transaction_id},
    )


def entity_count(level: str, search: str) -> int:
    df = query(
        """
        SELECT COUNT(*) AS n
        FROM behavior.entity_risk_profiles
        WHERE (:level = 'ALL' OR entity_risk_level = :level)
          AND (
              :search = ''
              OR CAST(entity_key AS TEXT) = :search
          )
        """,
        {"level": level, "search": search},
    )

    return int(df.iloc[0]["n"])


def entity_page(
    level: str,
    search: str,
    page: int,
    page_size: int,
):
    return query(
        """
        SELECT *
        FROM analytics.vw_entity_risk_leaderboard
        WHERE (:level = 'ALL' OR entity_risk_level = :level)
          AND (
              :search = ''
              OR CAST(entity_key AS TEXT) = :search
          )
        ORDER BY entity_risk_score DESC, entity_key
        LIMIT :limit OFFSET :offset
        """,
        {
            "level": level,
            "search": search,
            "limit": page_size,
            "offset": (page - 1) * page_size,
        },
    )


def entity_detail(entity_key: str):
    return query(
        """
        SELECT *
        FROM analytics.vw_entity_risk_leaderboard
        WHERE CAST(entity_key AS TEXT) = :entity_key
        """,
        {"entity_key": entity_key},
    )


def entity_activity(entity_key: str):
    return query(
        """
        SELECT *
        FROM behavior.entity_daily_activity
        WHERE CAST(entity_key AS TEXT) = :entity_key
        ORDER BY date_key
        """,
        {"entity_key": entity_key},
    )


def entity_counterparties(entity_key: str):
    return query(
        """
        WITH edges AS (
            SELECT
                CAST(receiver_entity_key AS TEXT)
                    AS counterparty,
                'OUTGOING' AS direction,
                COUNT(*) AS tx_count
            FROM warehouse.fact_transactions
            WHERE CAST(sender_entity_key AS TEXT) = :entity_key
            GROUP BY receiver_entity_key

            UNION ALL

            SELECT
                CAST(sender_entity_key AS TEXT)
                    AS counterparty,
                'INCOMING' AS direction,
                COUNT(*) AS tx_count
            FROM warehouse.fact_transactions
            WHERE CAST(receiver_entity_key AS TEXT) = :entity_key
            GROUP BY sender_entity_key
        )
        SELECT *
        FROM edges
        ORDER BY tx_count DESC, counterparty
        LIMIT 30
        """,
        {"entity_key": entity_key},
    )


def detection_effectiveness():
    return query(
        """
        SELECT *
        FROM analytics.vw_detection_effectiveness
        """
    )


def validation_snapshot():
    return query(
        """
        SELECT
            (SELECT COUNT(*)
             FROM warehouse.fact_transactions) AS facts,

            (SELECT COUNT(*)
             FROM risk.transaction_scores) AS scores,

            (SELECT COUNT(*)
             FROM risk.alerts) AS alerts,

            (SELECT COUNT(*)
             FROM behavior.entity_daily_activity) AS activity,

            (SELECT COUNT(*)
             FROM behavior.entity_daily_signals) AS signals,

            (SELECT COUNT(*)
             FROM behavior.entity_daily_advanced) AS advanced,

            (SELECT COUNT(*)
             FROM behavior.entity_risk_profiles) AS profiles,

            (SELECT COUNT(*)
             FROM warehouse.dim_entity) AS entities
        """
    )


def operational_counts():
    return query(
        """
        SELECT 'Warehouse Transactions' AS dataset,
               COUNT(*) AS row_count
        FROM warehouse.fact_transactions

        UNION ALL

        SELECT 'Transaction Risk Scores', COUNT(*)
        FROM risk.transaction_scores

        UNION ALL

        SELECT 'Alerts', COUNT(*)
        FROM risk.alerts

        UNION ALL

        SELECT 'Entity Daily Activity', COUNT(*)
        FROM behavior.entity_daily_activity

        UNION ALL

        SELECT 'Entity Daily Signals', COUNT(*)
        FROM behavior.entity_daily_signals

        UNION ALL

        SELECT 'Entity Advanced Signals', COUNT(*)
        FROM behavior.entity_daily_advanced

        UNION ALL

        SELECT 'Entity Risk Profiles', COUNT(*)
        FROM behavior.entity_risk_profiles
        """
    )
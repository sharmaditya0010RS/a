import os

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


@st.cache_resource
def engine():
    url = os.getenv('DATABASE_URL')
    if not url:
        url = URL.create('postgresql+psycopg', username=os.getenv('PGUSER', 'aml_user'), password=os.getenv('PGPASSWORD', ''), host=os.getenv('PGHOST', '127.0.0.1'), port=int(os.getenv('PGPORT', '55432')), database=os.getenv('PGDATABASE', 'aml_analytics'))
    return create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=5, connect_args={'connect_timeout': 8})


@st.cache_data(ttl=180, show_spinner=False)
def query(sql: str, params: dict | None = None) -> pd.DataFrame:
    with engine().connect() as conn:
        return pd.read_sql_query(text(sql), conn, params=params or {})


def scalar(sql: str, params: dict | None = None):
    df = query(sql, params)
    return df.iat[0, 0] if not df.empty else None


def fmt(n):
    return f'{int(n):,}' if pd.notna(n) else '—'


def sidebar():
    with st.sidebar:
        st.caption('GLOBAL FINANCIAL CRIME INTELLIGENCE')
        st.title('Risk Command Center')
        st.caption('PostgreSQL-backed • Synthetic AML data')
        st.divider()
        if st.button('↻ Refresh cached data', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        st.caption('Read-only analytics • 3-minute query cache')


def overview():
    st.title('Executive Overview')
    st.caption('Operational monitoring and risk exposure • all amounts are currency-specific')
    k = query('SELECT * FROM analytics.vw_executive_kpis').iloc[0]
    cols = st.columns(4)
    for col, label, key in zip(cols, ['Transactions', 'AML-positive labels', 'Transaction alerts', 'High-risk entities'], ['total_transactions', 'aml_positive_transactions', 'total_alerts', 'high_risk_entities'], strict=True):
        col.metric(label, fmt(k[key]))
    st.metric('Alert rate', f"{float(k['alert_rate_pct']):.2f}%")
    trends = query('SELECT * FROM analytics.vw_daily_risk_trends ORDER BY full_date')
    if not trends.empty:
        trends['full_date'] = pd.to_datetime(trends['full_date'])
        st.subheader('Daily transaction and alert volume')
        st.line_chart(trends.set_index('full_date')[['transaction_count', 'alert_count']])
        st.subheader('Daily AML-positive ground truth')
        st.bar_chart(trends.set_index('full_date')[['aml_positive_count']])
    st.subheader('Entity risk distribution')
    dist = query('SELECT entity_risk_level, COUNT(*) AS entities FROM behavior.entity_risk_profiles GROUP BY 1 ORDER BY 1')
    st.dataframe(dist, use_container_width=True, hide_index=True)


def investigations():
    st.title('Alert Investigation')
    st.caption('Prioritization queue • transaction risk is not proof of criminal activity')
    a, b, c = st.columns([1, 1, 2])
    with a:
        level = st.selectbox('Risk level', ['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'])
    with b:
        status = st.selectbox('Status', ['ALL', 'OPEN', 'IN_REVIEW', 'CLOSED'])
    with c:
        entity = st.text_input('Sender entity key (exact match)', '').strip()
    page_size = 100
    page = st.number_input('Page', min_value=1, value=1, step=1)
    where = "WHERE (:level = 'ALL' OR risk_level = :level) AND (:status = 'ALL' OR alert_status = :status) AND (:entity = '' OR sender_entity_key = :entity)"
    params = {'level': level, 'status': status, 'entity': entity}
    count = scalar(f'SELECT COUNT(*) FROM analytics.vw_investigation_queue {where}', params)
    st.caption(f'{fmt(count)} matching alerts • {page_size} per page')
    rows = query(f'''SELECT alert_id, transaction_id, transaction_timestamp, risk_level, risk_score, alert_status, sender_entity_key, receiver_entity_key, amount_paid, payment_currency_key, triggered_rules, sender_entity_risk_level FROM analytics.vw_investigation_queue {where} ORDER BY risk_score DESC, alert_id LIMIT :limit OFFSET :offset''', {**params, 'limit': page_size, 'offset': (int(page) - 1) * page_size})
    st.dataframe(rows, use_container_width=True, hide_index=True)
    st.caption('Amounts are denominated in payment_currency_key; do not aggregate across currencies.')
    if not rows.empty:
        txid = st.selectbox('Inspect transaction', rows['transaction_id'].astype(str).tolist())
        hits = query('SELECT rule_code, detected_at FROM risk.rule_hits WHERE transaction_id = :id ORDER BY rule_code', {'id': int(txid)})
        st.subheader('Rule evidence')
        st.dataframe(hits, use_container_width=True, hide_index=True)
    st.info('Read-only investigation view. Changing alert statuses requires a separately authenticated, audited workflow.')


def entities():
    st.title('Entity & Network Intelligence')
    st.caption('Explainable account-level behavioural profiles')
    level = st.selectbox('Entity risk', ['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'])
    key = st.text_input('Entity key (exact match)', '').strip()
    limit = st.slider('Results', 25, 250, 100, 25)
    where = "WHERE (:level = 'ALL' OR entity_risk_level = :level) AND (:key = '' OR entity_key = :key)"
    rows = query(f'''SELECT entity_key, bank_id, account_id, entity_risk_score, entity_risk_level, active_days, outgoing_transactions, incoming_transactions, velocity_days, fan_in_days, fan_out_days, high_behavior_days, rapid_movement_count, structuring_candidate_days FROM analytics.vw_entity_risk_leaderboard {where} ORDER BY entity_risk_score DESC, rapid_movement_count DESC, entity_key LIMIT :limit''', {'level': level, 'key': key, 'limit': limit})
    st.dataframe(rows, use_container_width=True, hide_index=True)
    if not rows.empty:
        chosen = st.selectbox('Inspect entity', rows['entity_key'].astype(str).tolist())
        history = query('''SELECT d.full_date, s.behavior_score, s.behavior_level, s.velocity_flag, s.fan_in_flag, s.fan_out_flag, s.cross_currency_flag, s.high_value_flag, a.rapid_movement_count, a.structuring_candidate_count FROM behavior.entity_daily_signals s JOIN warehouse.dim_date d ON d.date_key = s.date_key JOIN behavior.entity_daily_advanced a ON a.entity_key = s.entity_key AND a.date_key = s.date_key WHERE s.entity_key = :key ORDER BY d.full_date''', {'key': chosen})
        st.subheader('Daily risk signals')
        st.dataframe(history, use_container_width=True, hide_index=True)
    st.info('Rapid movement = temporal proximity, not confirmed tracing. Structuring = heuristic candidate, not regulatory determination.')


def performance():
    st.title('Detection Performance')
    st.caption('Evaluation against synthetic ground-truth AML labels; not real-world production accuracy')
    m = query('SELECT * FROM analytics.vw_detection_effectiveness').iloc[0]
    cols = st.columns(4)
    for col, label, key in zip(cols, ['Precision', 'Recall', 'F1 score', 'False-positive rate'], ['precision', 'recall', 'f1_score', 'false_positive_rate'], strict=True):
        col.metric(label, f"{100 * float(m[key]):.2f}%" if pd.notna(m[key]) else 'N/A')
    st.subheader('Confusion matrix')
    matrix = pd.DataFrame({'Predicted alert': [int(m['true_positives']), int(m['false_positives'])], 'Predicted no alert': [int(m['false_negatives']), int(m['true_negatives'])]}, index=['Actually AML-positive', 'Actually AML-negative'])
    st.dataframe(matrix, use_container_width=True)
    st.caption('These metrics evaluate Phase 6 transaction alerts, not Phase 7 entity profile classifications.')


def operations():
    st.title('Data Quality & Operations')
    st.caption('Read-only completeness and reconciliation monitoring')
    metrics = query('''SELECT (SELECT COUNT(*) FROM warehouse.fact_transactions) AS fact_transactions, (SELECT COUNT(*) FROM risk.transaction_scores) AS transaction_scores, (SELECT COUNT(*) FROM behavior.entity_daily_activity) AS entity_daily_activity, (SELECT COUNT(*) FROM behavior.entity_daily_signals) AS entity_daily_signals, (SELECT COUNT(*) FROM behavior.entity_daily_advanced) AS entity_daily_advanced, (SELECT COUNT(*) FROM behavior.entity_risk_profiles) AS entity_profiles, (SELECT COUNT(*) FROM behavior.rapid_movement) AS rapid_movement_pairs''').iloc[0]
    st.dataframe(pd.DataFrame({'Dataset': list(metrics.index), 'Rows': [int(x) for x in metrics.values]}), hide_index=True, use_container_width=True)
    checks = {'Transaction scoring reconciliation': metrics['fact_transactions'] == metrics['transaction_scores'], 'Entity-day scoring reconciliation': metrics['entity_daily_activity'] == metrics['entity_daily_signals'], 'Advanced daily reconciliation': metrics['entity_daily_activity'] == metrics['entity_daily_advanced']}
    for name, ok in checks.items():
        (st.success if ok else st.error)(f"{'PASS' if ok else 'FAIL'} — {name}")
    last = query('''SELECT MAX(scored_at) AS last_transaction_scored FROM risk.transaction_scores''').iloc[0, 0]
    st.caption(f'Last transaction score timestamp: {last}')

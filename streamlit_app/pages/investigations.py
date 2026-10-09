import math

import streamlit as st

from streamlit_app.db import (
    alert_count,
    alert_detail,
    alert_page,
    alert_rule_hits,
)
from streamlit_app.insights import (
    bar_chart,
    explain,
    section,
)
from streamlit_app.theme import number

st.title("Alert Investigation Workbench")
st.caption(
    "Review high-priority alerts, understand the triggering "
    "evidence and examine transaction context."
)

section(
    "Investigation queue",
    "Filter the alerts requiring analyst attention.",
)

f1, f2, f3, f4 = st.columns([1, 1, 2, 1])

with f1:
    level = st.selectbox(
        "Risk level",
        ["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"],
    )

with f2:
    status = st.selectbox(
        "Alert status",
        ["ALL", "OPEN", "IN_REVIEW", "CLOSED"],
    )

with f3:
    search = st.text_input(
        "Alert or transaction ID",
        placeholder="Search by exact numeric ID",
    ).strip()

with f4:
    page_size = st.selectbox(
        "Rows per page",
        [25, 50, 100],
        index=1,
    )

if search and not search.isdigit():
    st.warning("Please enter a numeric identifier.")
    st.stop()

total = alert_count(level, status, search)
page_count = max(1, math.ceil(total / page_size))

c1, c2 = st.columns(2)
c1.metric("Matching Alerts", number(total))
c2.metric("Total Pages", number(page_count))

page = st.number_input(
    "Queue page",
    min_value=1,
    max_value=page_count,
    value=1,
)

alerts = alert_page(
    level,
    status,
    search,
    int(page),
    page_size,
)

if alerts.empty:
    st.info("No alerts match the selected filters.")
    st.stop()

st.dataframe(
    alerts,
    use_container_width=True,
    hide_index=True,
    height=400,
    column_config={
        "risk_score": st.column_config.ProgressColumn(
            "Risk Score",
            min_value=0,
            max_value=100,
        ),
    },
)

st.divider()

section(
    "Selected alert intelligence",
    "Choose a transaction to inspect its evidence.",
)

selected_id = st.selectbox(
    "Select alert",
    alerts["alert_id"].astype(int).tolist(),
)

details = alert_detail(selected_id)

if details.empty:
    st.error("The selected alert has no reporting detail.")
    st.stop()

alert = details.iloc[0]

score = float(alert["risk_score"])
risk_level = str(alert["risk_level"])
alert_status = str(alert["alert_status"])

c1, c2, c3, c4 = st.columns(4)

c1.metric("Risk Score", f"{score:.0f}/100")
c2.metric("Risk Level", risk_level)
c3.metric("Workflow Status", alert_status)
c4.metric(
    "Transaction ID",
    str(alert["transaction_id"]),
)

if risk_level == "CRITICAL":
    st.error(
        "Critical monitoring priority. Review according "
        "to the organization's escalation policy."
    )
elif risk_level == "HIGH":
    st.warning(
        "High monitoring priority. Analyst review is recommended."
    )
else:
    st.info(
        "This alert should be assessed using its supporting "
        "evidence and investigation context."
    )

left, right = st.columns(2)

with left:
    with st.container(border=True):
        st.subheader("Transaction details")
        st.write(
            "**Timestamp:**",
            alert["transaction_timestamp"],
        )
        st.write(
            "**Amount:**",
            f"{float(alert['amount_paid']):,.2f}",
        )
        st.write(
            "**Currency key:**",
            alert["payment_currency_key"],
        )
        st.write(
            "**Cross-currency:**",
            alert["is_cross_currency"],
        )

with right:
    with st.container(border=True):
        st.subheader("Entity context")
        st.write(
            "**Sender:**",
            alert["sender_entity_key"],
        )
        st.write(
            "**Receiver:**",
            alert["receiver_entity_key"],
        )
        st.write(
            "**Sender risk:**",
            alert["sender_entity_risk_level"],
        )
        st.write(
            "**Receiver risk:**",
            alert["receiver_entity_risk_level"],
        )

st.divider()

section(
    "Why did the rule engine flag this transaction?",
    "Review the recorded detection-rule evidence.",
)

rules = alert_rule_hits(int(alert["transaction_id"]))

if rules.empty:
    st.warning(
        "No rule-hit records were returned for this transaction."
    )
else:
    with st.container(border=True):
        bar_chart(
            rules,
            "rule_code",
            "hit_count",
            "Triggered Rule Evidence",
            horizontal=True,
        )

        st.dataframe(
            rules,
            use_container_width=True,
            hide_index=True,
        )

        explain(
            "Triggered Rule Evidence",
            (
                "Each bar shows how many rule-hit records "
                "were found for the selected transaction."
            ),
            (
                "This is an evidence count, not the number "
                "of confirmed suspicious activities."
            ),
            (
                "Compare the triggered rules with the transaction "
                "and sender/receiver context."
            ),
        )

st.divider()

section(
    "Investigator review checklist",
    "A guided process for non-technical analysts.",
)

with st.container(border=True):
    st.checkbox(
        "Confirm transaction ID, timestamp and currency",
        key=f"check_transaction_{selected_id}",
    )
    st.checkbox(
        "Review all triggered detection rules",
        key=f"check_rules_{selected_id}",
    )
    st.checkbox(
        "Review sender and receiver risk context",
        key=f"check_entities_{selected_id}",
    )
    st.checkbox(
        "Document whether further escalation is needed",
        key=f"check_escalation_{selected_id}",
    )

    st.caption(
        "These selections are temporary UI state. "
        "They do not save an investigation decision."
    )

st.info(
    "An alert is a request for review, not proof of "
    "money laundering or another financial crime."
)
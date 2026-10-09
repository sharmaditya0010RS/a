import pandas as pd
import streamlit as st

from streamlit_app.db import (
    alert_status_distribution,
    daily_trends,
    executive_kpis,
    risk_distribution,
    rule_distribution,
)
from streamlit_app.insights import (
    area_chart,
    bar_chart,
    donut_chart,
    explain,
    kpi,
    line_chart,
    section,
)
from streamlit_app.theme import (
    RISK_COLORS,
    compact_number,
    number,
    safe_divide,
)

st.title("Executive Command Center")
st.caption(
    "Enterprise-wide visibility into transaction monitoring, "
    "financial crime indicators and investigation workload."
)

kpis = executive_kpis()

if len(kpis) != 1:
    st.error("Executive KPI view must return exactly one row.")
    st.stop()

row = kpis.iloc[0]

transactions = int(row["total_transactions"])
alerts = int(row["total_alerts"])
positives = int(row["aml_positive_transactions"])
high_entities = int(row["high_risk_entities"])
open_alerts = int(row["open_alerts"])

if (
    transactions <= 0
    or alerts > transactions
    or positives > transactions
):
    st.error("Executive KPI integrity check failed.")
    st.stop()

alert_rate = safe_divide(alerts, transactions)

section(
    "Monitoring overview",
    "All-time platform KPIs from the PostgreSQL reporting view.",
)

c1, c2, c3, c4 = st.columns(4)

with c1:
    kpi(
        "Transactions Screened",
        compact_number(transactions),
        f"{number(transactions)} transactions evaluated",
    )

with c2:
    kpi(
        "Alerts Generated",
        compact_number(alerts),
        "Transactions flagged for review",
    )

with c3:
    kpi(
        "Alert Rate",
        f"{alert_rate:.2%}",
        "Share of transactions generating alerts",
    )

with c4:
    kpi(
        "High-Risk Entities",
        number(high_entities),
        "Entities classified HIGH or CRITICAL",
    )

st.info(
    f"**Executive takeaway:** The system screened "
    f"{number(transactions)} transactions and generated "
    f"{number(alerts)} alerts. This represents an alert rate "
    f"of {alert_rate:.2%}. Alerts indicate review priorities, "
    f"not confirmed financial crime."
)

st.divider()

section(
    "Transaction monitoring trends",
    "Track daily activity and identify changes requiring review.",
)

trends = daily_trends().copy()

if trends.empty:
    st.warning("Daily reporting data is unavailable.")
    st.stop()

trends["full_date"] = pd.to_datetime(
    trends["full_date"],
    errors="coerce",
)

if trends["full_date"].isna().any():
    st.error("Daily reporting view contains invalid dates.")
    st.stop()

trends = trends.sort_values("full_date")
available_dates = sorted(
    trends["full_date"].dt.date.unique().tolist()
)

if len(available_dates) == 1:
    start = end = available_dates[0]
    st.caption(f"Reporting date: {start}")
else:
    start, end = st.select_slider(
        "Reporting period",
        options=available_dates,
        value=(
            available_dates[0],
            available_dates[-1],
        ),
        format_func=lambda d: d.strftime("%d %b %Y"),
    )

filtered = trends.loc[
    trends["full_date"].dt.date.between(start, end)
].copy()

filtered["daily_alert_rate"] = filtered.apply(
    lambda r: safe_divide(
        float(r["alert_count"]),
        float(r["transaction_count"]),
    ),
    axis=1,
)

volume = int(filtered["transaction_count"].sum())
period_alerts = int(filtered["alert_count"].sum())
period_positives = int(
    filtered["aml_positive_count"].sum()
)

c1, c2, c3 = st.columns(3)

c1.metric("Selected-period Transactions", number(volume))
c2.metric("Selected-period Alerts", number(period_alerts))
c3.metric(
    "Selected-period Alert Rate",
    f"{safe_divide(period_alerts, volume):.2%}",
)

with st.container(border=True):
    area_chart(
        filtered,
        "full_date",
        "transaction_count",
        "Daily Transaction Activity",
    )

    explain(
        "Daily Transaction Activity",
        (
            "The chart shows how many payments entered "
            "monitoring on each reporting day."
        ),
        (
            "Sharp changes may reflect normal business activity "
            "or changes in processing and data coverage."
        ),
        "Review unusual days against source data and alert volume.",
    )

left, right = st.columns(2)

with left:
    with st.container(border=True):
        line_chart(
            filtered,
            "full_date",
            {
                "alert_count": "Generated Alerts",
                "aml_positive_count": "Synthetic AML Labels",
            },
            "Alerts vs Reference Labels",
        )

        explain(
            "Alerts vs Reference Labels",
            (
                "The two lines compare daily alert counts "
                "with daily synthetic AML-positive labels."
            ),
            (
                "Similar daily totals do not establish that "
                "the correct transactions were detected."
            ),
            "Check the confusion matrix on Detection Performance.",
        )

with right:
    with st.container(border=True):
        line_chart(
            filtered,
            "full_date",
            {"daily_alert_rate": "Alert Rate"},
            "Daily Alert Rate",
            percent=True,
        )

        explain(
            "Daily Alert Rate",
            (
                "This shows the share of each day's transactions "
                "that generated alerts."
            ),
            (
                "A rising rate may increase investigator workload "
                "or indicate a change in monitored patterns."
            ),
            "Review alert quality before adjusting rules.",
        )

st.divider()

section(
    "Risk concentration",
    "Understand where monitoring attention is focused.",
)

left, right = st.columns(2)

with left:
    with st.container(border=True):
        risk = risk_distribution()

        donut_chart(
            risk,
            "risk_level",
            "entity_count",
            "Entity Risk Distribution",
            color_map=RISK_COLORS,
        )

        explain(
            "Entity Risk Distribution",
            (
                "The chart shows the number of entities "
                "in each risk classification."
            ),
            (
                "HIGH and CRITICAL entities are prioritized "
                "for investigation, not automatically guilty."
            ),
            "Open Entity Intelligence to review their behaviour.",
        )

with right:
    with st.container(border=True):
        statuses = alert_status_distribution()

        bar_chart(
            statuses,
            "alert_status",
            "alert_count",
            "Investigation Workload by Status",
        )

        explain(
            "Investigation Workload",
            (
                f"There are currently {number(open_alerts)} "
                "OPEN alerts in the all-time reporting snapshot."
            ),
            (
                "An increasing open queue can indicate "
                "investigation capacity pressure."
            ),
            "Prioritize alerts based on risk and available evidence.",
        )

st.divider()

section(
    "Detection rule activity",
    "Identify which monitoring rules are triggered most often.",
)

rules = rule_distribution()

with st.container(border=True):
    bar_chart(
        rules.head(15),
        "rule_code",
        "triggered_transactions",
        "Top Detection Rules by Hit Count",
        horizontal=True,
        height=410,
    )

    explain(
        "Rule Activity",
        (
            "The chart ranks rules by the number of "
            "recorded rule-hit events."
        ),
        (
            "One transaction can trigger multiple rules. "
            "Therefore, rule-hit counts should not be added "
            "together as unique alert counts."
        ),
        "Review individual rule quality and false positives.",
    )

with st.expander("Business glossary"):
    st.markdown(
        """
        **Transaction:** A payment event in the dataset.

        **Alert:** A transaction flagged for investigation.

        **Risk score:** A rule-derived prioritization score.

        **Entity:** An account or customer representation.

        **AML-positive label:** A synthetic reference label.

        **False positive:** An alerted transaction labeled negative.

        **Recall:** Share of positive-labeled transactions detected.
        """
    )

st.caption(
    "Date filters apply to daily charts and selected-period KPIs. "
    "The four top cards remain all-time values."
)
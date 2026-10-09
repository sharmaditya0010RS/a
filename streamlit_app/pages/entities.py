import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from streamlit_app.db import (
    entity_activity,
    entity_count,
    entity_counterparties,
    entity_detail,
    entity_page,
)
from streamlit_app.insights import (
    bar_chart,
    explain,
    section,
)
from streamlit_app.theme import (
    BLUE,
    TEAL,
    number,
    style_chart,
)

st.title("Entity Intelligence Center")
st.caption(
    "Understand entity risk, behavioural signals and "
    "transaction relationships."
)

section(
    "Entity risk leaderboard",
    "Identify accounts with the strongest monitoring indicators.",
)

f1, f2, f3 = st.columns([1, 2, 1])

with f1:
    level = st.selectbox(
        "Risk classification",
        ["HIGH", "CRITICAL", "MEDIUM", "LOW", "ALL"],
    )

with f2:
    search = st.text_input(
        "Entity identifier",
        placeholder="Enter an exact entity key",
    ).strip()

with f3:
    page_size = st.selectbox(
        "Rows per page",
        [25, 50, 100],
        index=1,
    )

total = entity_count(level, search)
page_count = max(1, math.ceil(total / page_size))

c1, c2 = st.columns(2)
c1.metric("Matching Entities", number(total))
c2.metric("Leaderboard Pages", number(page_count))

page = st.number_input(
    "Leaderboard page",
    min_value=1,
    max_value=page_count,
    value=1,
)

entities = entity_page(
    level,
    search,
    int(page),
    page_size,
)

if entities.empty:
    st.info("No entities match the current filters.")
    st.stop()

st.dataframe(
    entities,
    use_container_width=True,
    hide_index=True,
    height=380,
    column_config={
        "entity_risk_score": st.column_config.ProgressColumn(
            "Entity Risk Score",
            min_value=0,
            max_value=100,
        ),
    },
)

st.divider()

section(
    "Entity deep dive",
    "Inspect one entity's monitoring profile and relationships.",
)

selected = st.selectbox(
    "Select entity",
    entities["entity_key"].astype(str).tolist(),
)

detail = entity_detail(selected)

if detail.empty:
    st.error("Selected entity details are unavailable.")
    st.stop()

entity = detail.iloc[0]

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Risk Score",
    f"{float(entity['entity_risk_score']):.0f}/100",
)

c2.metric(
    "Risk Level",
    str(entity["entity_risk_level"]),
)

c3.metric(
    "Rapid Movement Pairs",
    number(entity["rapid_movement_count"]),
)

c4.metric(
    "Structuring Candidate Days",
    number(entity["structuring_candidate_days"]),
)

st.info(
    "**Interpretation:** The risk score prioritizes entities "
    "for review. Rapid movement reflects transaction timing, "
    "not proven movement of the same funds. Structuring "
    "candidates are heuristic indicators."
)

st.divider()

section(
    "Behavioural indicators",
    "Understand which patterns contributed to monitoring concern.",
)

features = pd.DataFrame(
    [
        {
            "indicator": "Velocity",
            "days": int(entity["velocity_days"]),
        },
        {
            "indicator": "Fan-in",
            "days": int(entity["fan_in_days"]),
        },
        {
            "indicator": "Fan-out",
            "days": int(entity["fan_out_days"]),
        },
        {
            "indicator": "High Behaviour",
            "days": int(entity["high_behavior_days"]),
        },
    ]
)

with st.container(border=True):
    bar_chart(
        features,
        "indicator",
        "days",
        "Days with Behavioural Risk Indicators",
    )

    explain(
        "Behavioural Indicators",
        (
            "The chart counts days when different "
            "monitoring patterns were detected."
        ),
        (
            "Repeated patterns may justify investigation, "
            "but each pattern can have legitimate explanations."
        ),
        (
            "Review historical activity and expected "
            "business behaviour before escalation."
        ),
    )

st.divider()

section(
    "Historical activity",
    "Explore the entity's recorded daily behaviour.",
)

activity = entity_activity(selected)

if activity.empty:
    st.info("No daily activity records found.")
else:
    st.dataframe(
        activity,
        use_container_width=True,
        hide_index=True,
        height=300,
    )

st.divider()

section(
    "Counterparty network",
    "See which other entities transact most frequently with this account.",
)

counterparties = entity_counterparties(selected)

if counterparties.empty:
    st.info("No counterparty relationships found.")
else:
    top = counterparties.head(20).copy()

    with st.container(border=True):
        fig = go.Figure()

        for direction, color in [
            ("OUTGOING", BLUE),
            ("INCOMING", TEAL),
        ]:
            subset = top.loc[
                top["direction"] == direction
            ]

            fig.add_trace(
                go.Bar(
                    x=subset["tx_count"],
                    y=subset["counterparty"].astype(str),
                    orientation="h",
                    name=direction.title(),
                    marker_color=color,
                    hovertemplate=(
                        "Counterparty: %{y}<br>"
                        "Transactions: %{x:,}<extra></extra>"
                    ),
                )
            )

        fig.update_layout(
            title="Most Frequent Counterparty Connections",
            barmode="group",
            xaxis_title="Number of Transactions",
            yaxis_title="Counterparty",
            yaxis={"autorange": "reversed"},
        )

        st.plotly_chart(
            style_chart(fig, 480),
            use_container_width=True,
        )

        explain(
            "Counterparty Connections",
            (
                "The bars show how often this entity "
                "sent to or received from counterparties."
            ),
            (
                "High transaction frequency does not "
                "automatically indicate suspicious activity."
            ),
            (
                "Review concentration, transaction direction "
                "and the entity's normal business purpose."
            ),
        )

    with st.expander("View counterparty records"):
        st.dataframe(
            counterparties,
            use_container_width=True,
            hide_index=True,
        )

st.caption(
    "Transaction counts are used for comparisons. "
    "Amounts in different currencies are not combined."
)
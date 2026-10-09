from __future__ import annotations

import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from streamlit_app.case_export import case_export_section
from streamlit_app.investigation_db import (
    alert_evidence,
    counterparty_network,
    entity_profile,
    investigation_queue,
    priority_summary,
    queue_count,
    related_transactions,
    triggered_rules,
)
from streamlit_app.theme import (
    AMBER,
    BLUE,
    RED,
    TEAL,
    apply_styles,
    style_chart,
)

PAGE_SIZE = 25

PRIORITY_COLORS = {
    "P1": RED,
    "P2": AMBER,
    "P3": BLUE,
    "P4": TEAL,
}


def render_overview() -> None:
    summary = priority_summary()

    counts = {
        str(row["priority_tier"]): int(row["alert_count"])
        for _, row in summary.iterrows()
    }

    columns = st.columns(5)

    with columns[0]:
        st.metric("Total alerts", f"{sum(counts.values()):,}")

    for column, tier in zip(
        columns[1:],
        ("P1", "P2", "P3", "P4"),
        strict=True,
    ):
        with column:
            st.metric(
                f"{tier} alerts",
                f"{counts.get(tier, 0):,}",
            )

    with st.container(border=True):
        st.subheader("Investigation Priority Distribution")

        fig = go.Figure()

        for tier in ("P1", "P2", "P3", "P4"):
            count = counts.get(tier, 0)

            fig.add_trace(
                go.Bar(
                    x=[tier],
                    y=[count],
                    name=tier,
                    marker_color=PRIORITY_COLORS[tier],
                    text=[f"{count:,}"],
                    textposition="outside",
                )
            )

        fig.update_layout(
            showlegend=False,
            bargap=0.4,
            yaxis_title="Alerts",
        )

        st.plotly_chart(
            style_chart(
                fig,
                height=280,
                show_legend=False,
            ),
            use_container_width=True,
            config={"displayModeBar": False},
        )


def render_queue() -> int | None:
    with st.container(border=True):
        st.subheader("Prioritized Investigation Queue")

        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            tier = st.selectbox(
                "Priority",
                ["ALL", "P1", "P2", "P3", "P4"],
                key="final_priority",
            )

        with col2:
            status = st.selectbox(
                "Status",
                ["ALL", "OPEN", "IN_REVIEW", "CLOSED"],
                key="final_status",
            )

        with col3:
            search = st.text_input(
                "Alert / Transaction ID",
                placeholder="Exact numeric ID",
                key="final_search",
            ).strip()

        if search and not search.isdecimal():
            st.warning("Enter a numeric identifier.")
            return None

        filters = (tier, status, search)

        if st.session_state.get("final_filters") != filters:
            st.session_state["final_filters"] = filters
            st.session_state["final_page"] = 1
            st.session_state.pop(
                "prepared_case_report",
                None,
            )

        total = queue_count(tier, status, search)
        max_page = max(1, math.ceil(total / PAGE_SIZE))

        current_page = min(
            int(st.session_state.get("final_page", 1)),
            max_page,
        )

        st.session_state["final_page"] = current_page

        col1, col2 = st.columns([3, 1])

        with col1:
            st.metric("Matching alerts", f"{total:,}")

        with col2:
            page = st.number_input(
                "Queue page",
                min_value=1,
                max_value=max_page,
                step=1,
                key="final_page",
            )

        if total == 0:
            st.info(
                "No alerts match the selected filters."
            )
            return None

        queue = investigation_queue(
            tier=tier,
            status=status,
            search_id=search,
            limit=PAGE_SIZE,
            offset=(int(page) - 1) * PAGE_SIZE,
        )

        if tier != "ALL":
            queue = queue.loc[
                queue["priority_tier"] == tier
            ]

        if status != "ALL":
            queue = queue.loc[
                queue["alert_status"] == status
            ]

        if queue.empty:
            st.warning(
                "No results returned for the current page."
            )
            return None

        display_columns = [
            "alert_id",
            "priority_tier",
            "investigation_priority_score",
            "transaction_risk_score",
            "alert_status",
            "transaction_id",
            "payment_currency_key",
        ]

        st.dataframe(
            queue[display_columns],
            hide_index=True,
            use_container_width=True,
            column_config={
                "alert_id": st.column_config.NumberColumn(
                    "Alert ID",
                    format="%d",
                ),
                "priority_tier": "Priority",
                "investigation_priority_score":
                    st.column_config.ProgressColumn(
                        "Priority score",
                        min_value=0,
                        max_value=100,
                    ),
                "transaction_risk_score":
                    "Transaction risk",
                "alert_status": "Status",
                "transaction_id": "Transaction ID",
                "payment_currency_key": "Currency",
            },
        )

        st.caption(
            f"Page {int(page):,} of {max_page:,} "
            f"| {len(queue):,} records shown"
        )

        alert_ids = [
            int(value)
            for value in queue["alert_id"].tolist()
        ]

        selected = st.selectbox(
            "Select an alert for investigation",
            alert_ids,
            format_func=lambda value: f"Alert #{value:,}",
            key=(
                f"final_alert_{tier}_{status}_"
                f"{search}_{page}"
            ),
        )

        return int(selected)


def render_score(record: pd.Series) -> None:
    components = [
        (
            "Transaction risk",
            int(record["transaction_component"]),
            BLUE,
        ),
        (
            "Entity risk",
            int(record["entity_component"]),
            TEAL,
        ),
        (
            "Dual high-risk bonus",
            int(record["dual_high_risk_component"]),
            AMBER,
        ),
    ]

    fig = go.Figure()

    for name, value, color in components:
        fig.add_trace(
            go.Bar(
                x=[value],
                y=["Priority score"],
                name=name,
                orientation="h",
                marker_color=color,
                text=f"+{value}",
                textposition="inside",
            )
        )

    fig.update_layout(
        barmode="stack",
        xaxis={
            "range": [0, 100],
            "title": "Priority points",
        },
    )

    st.plotly_chart(
        style_chart(fig, height=250),
        use_container_width=True,
        config={"displayModeBar": False},
    )

    st.caption(
        "Priority is a heuristic triage score, "
        "not a probability of criminal conduct."
    )


def render_entity_profile(
    label: str,
    entity_key: str,
) -> None:
    with st.expander(
        f"{label}: {entity_key}",
        expanded=False,
    ):
        profile = entity_profile(entity_key)

        if profile.empty:
            st.info("Entity profile unavailable.")
            return

        item = profile.iloc[0]

        st.metric(
            "Entity risk score",
            int(item["entity_risk_score"]),
        )

        st.caption(
            f"Risk level: {item['entity_risk_level']}"
        )

        columns = [
            "active_days",
            "outgoing_transactions",
            "incoming_transactions",
            "velocity_days",
            "fan_in_days",
            "fan_out_days",
            "high_behavior_days",
            "rapid_movement_count",
            "structuring_candidate_days",
        ]

        available = [
            column
            for column in columns
            if column in profile.columns
        ]

        st.dataframe(
            profile[available],
            hide_index=True,
            use_container_width=True,
        )


def render_evidence(record: pd.Series) -> None:
    alert_id = int(record["alert_id"])
    transaction_id = int(record["transaction_id"])

    with st.container(border=True):
        st.subheader(f"Alert #{alert_id:,} — Evidence Review")

        columns = st.columns(4)

        with columns[0]:
            st.metric(
                "Priority",
                str(record["priority_tier"]),
            )

        with columns[1]:
            st.metric(
                "Priority score",
                int(
                    record[
                        "investigation_priority_score"
                    ]
                ),
            )

        with columns[2]:
            st.metric(
                "Transaction risk",
                int(record["transaction_risk_score"]),
            )

        with columns[3]:
            st.metric(
                "Alert status",
                str(record["alert_status"]),
            )

        score_tab, evidence_tab, entity_tab = st.tabs(
            [
                "Risk explanation",
                "Transaction & rules",
                "Entity profiles",
            ]
        )

        with score_tab:
            render_score(record)

        with evidence_tab:
            details = pd.DataFrame(
                [
                    {
                        "Transaction ID": transaction_id,
                        "Timestamp": record[
                            "transaction_timestamp"
                        ],
                        "Sender": record[
                            "sender_entity_key"
                        ],
                        "Receiver": record[
                            "receiver_entity_key"
                        ],
                        "Amount paid": record[
                            "amount_paid"
                        ],
                        "Currency": record[
                            "payment_currency_key"
                        ],
                        "Cross currency": record[
                            "is_cross_currency"
                        ],
                    }
                ]
            )

            st.dataframe(
                details,
                hide_index=True,
                use_container_width=True,
            )

            st.markdown("**Triggered detection rules**")

            rules = triggered_rules(transaction_id)

            if rules.empty:
                st.info("No recorded rule hits.")
            else:
                st.dataframe(
                    rules,
                    hide_index=True,
                    use_container_width=True,
                )

        with entity_tab:
            render_entity_profile(
                "Sender",
                str(record["sender_entity_key"]),
            )

            render_entity_profile(
                "Receiver",
                str(record["receiver_entity_key"]),
            )


def render_relationships(entity_key: str) -> None:
    relationships = counterparty_network(
        entity_key,
        limit=12,
    )

    if relationships.empty:
        st.info("No counterparties found.")
        return

    data = relationships.sort_values(
        "transaction_count",
        ascending=True,
    )

    fig = go.Figure(
        go.Bar(
            x=data["transaction_count"],
            y=data["counterparty_key"],
            orientation="h",
            marker_color=BLUE,
        )
    )

    fig.update_layout(
        xaxis_title="Observed transactions",
        yaxis_title="",
    )

    st.plotly_chart(
        style_chart(
            fig,
            height=430,
            show_legend=False,
        ),
        use_container_width=True,
        config={"displayModeBar": False},
    )

    st.dataframe(
        relationships,
        hide_index=True,
        use_container_width=True,
    )

    st.caption(
        "Observed transaction relationships do not "
        "establish illicit coordination."
    )


def render_timeline(entity_key: str) -> None:
    activity = related_transactions(
        entity_key,
        limit=100,
    )

    if activity.empty:
        st.info("No recent transactions found.")
        return

    activity = activity.copy()

    activity["transaction_timestamp"] = pd.to_datetime(
        activity["transaction_timestamp"]
    )

    activity["direction"] = activity[
        "sender_entity_key"
    ].map(
        lambda value: (
            "OUTGOING"
            if value == entity_key
            else "INCOMING"
        )
    )

    activity["activity_date"] = activity[
        "transaction_timestamp"
    ].dt.date

    daily = (
        activity.groupby(
            ["activity_date", "direction"],
            as_index=False,
        )
        .size()
        .rename(
            columns={"size": "transaction_count"}
        )
    )

    fig = go.Figure()

    for direction, color in [
        ("INCOMING", BLUE),
        ("OUTGOING", AMBER),
    ]:
        subset = daily.loc[
            daily["direction"] == direction
        ]

        fig.add_trace(
            go.Bar(
                x=subset["activity_date"],
                y=subset["transaction_count"],
                name=direction.title(),
                marker_color=color,
            )
        )

    fig.update_layout(
        barmode="group",
        xaxis_title="Date",
        yaxis_title="Transaction count",
    )

    st.plotly_chart(
        style_chart(fig, height=300),
        use_container_width=True,
        config={"displayModeBar": False},
    )

    st.dataframe(
        activity.sort_values(
            "transaction_timestamp",
            ascending=False,
        ),
        hide_index=True,
        use_container_width=True,
    )

    st.caption(
        "Timeline represents the latest 100 retrieved "
        "transactions, not complete account history."
    )


def main() -> None:
    apply_styles()

    st.title("Advanced Investigation Workbench")

    st.caption(
        "Financial Crime Intelligence | "
        "Evidence-based alert triage and case reporting"
    )

    st.info(
        "Read-only investigation support. "
        "Synthetic AML research environment."
    )

    try:
        render_overview()

        st.divider()

        alert_id = render_queue()

        if alert_id is None:
            return

        evidence = alert_evidence(alert_id)

        if evidence.empty:
            st.warning(
                "Evidence is unavailable for this alert."
            )
            return

        record = evidence.iloc[0]

        st.divider()

        render_evidence(record)

        st.divider()

        st.subheader("Connected Entity Intelligence")

        sender = str(record["sender_entity_key"])
        receiver = str(record["receiver_entity_key"])

        entities = list(
            dict.fromkeys([sender, receiver])
        )

        selected_entity = st.selectbox(
            "Entity under review",
            entities,
            key=f"final_entity_{alert_id}",
        )

        network_tab, timeline_tab = st.tabs(
            [
                "Counterparty relationships",
                "Transaction timeline",
            ]
        )

        with network_tab:
            render_relationships(selected_entity)

        with timeline_tab:
            render_timeline(selected_entity)

        st.divider()

        case_export_section(alert_id)

    except Exception as exc:
        st.error(
            "Investigation workbench encountered an error."
        )
        st.exception(exc)


main()
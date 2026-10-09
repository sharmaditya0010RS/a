import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from streamlit_app.theme import (
    AMBER,
    BLUE,
    CHART_COLORS,
    RED,
    TEAL,
    style_chart,
)


def section(
    title: str,
    description: str,
) -> None:
    st.subheader(title)
    st.caption(description)


def explain(
    title: str,
    meaning: str,
    importance: str,
    action: str,
) -> None:
    with st.container(border=True):
        st.markdown(f"**What does {title} tell us?**")
        st.write(meaning)

        with st.expander("Business interpretation & next action"):
            st.markdown(f"**Why it matters:** {importance}")
            st.markdown(f"**Recommended action:** {action}")


def kpi(
    label: str,
    value: str,
    description: str,
    *,
    delta: str | None = None,
) -> None:
    st.metric(
        label=label,
        value=value,
        delta=delta,
    )
    st.caption(description)


def line_chart(
    df: pd.DataFrame,
    x: str,
    series: dict[str, str],
    title: str,
    *,
    percent: bool = False,
    height: int = 340,
) -> None:
    if df.empty:
        st.info("No data for the selected period.")
        return

    fig = go.Figure()

    for index, (column, label) in enumerate(series.items()):
        color = CHART_COLORS[index % len(CHART_COLORS)]

        fig.add_trace(
            go.Scatter(
                x=df[x],
                y=df[column],
                mode="lines+markers",
                name=label,
                line={
                    "color": color,
                    "width": 3,
                    "shape": "spline",
                    "smoothing": 0.5,
                },
                marker={
                    "size": 6,
                    "color": color,
                },
                hovertemplate=(
                    "%{x}<br>"
                    + label
                    + ": %{y:,.2f}<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title=title,
        hovermode="x unified",
    )

    if percent:
        fig.update_yaxes(tickformat=".1%")
    else:
        fig.update_yaxes(tickformat=",.0f")

    st.plotly_chart(
        style_chart(fig, height),
        use_container_width=True,
    )


def area_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
) -> None:
    if df.empty:
        st.info("No data available.")
        return

    fig = go.Figure(
        go.Scatter(
            x=df[x],
            y=df[y],
            mode="lines",
            fill="tozeroy",
            line={
                "color": TEAL,
                "width": 3,
            },
            fillcolor="rgba(45,212,191,0.12)",
            hovertemplate="%{x}<br>%{y:,.0f}<extra></extra>",
        )
    )

    fig.update_layout(title=title)

    st.plotly_chart(
        style_chart(fig),
        use_container_width=True,
    )


def bar_chart(
    df: pd.DataFrame,
    category: str,
    value: str,
    title: str,
    *,
    horizontal: bool = False,
    height: int = 340,
) -> None:
    if df.empty:
        st.info("No data available.")
        return

    fig = go.Figure(
        go.Bar(
            x=df[value] if horizontal else df[category],
            y=df[category] if horizontal else df[value],
            orientation="h" if horizontal else "v",
            marker={
                "color": TEAL,
                "line": {"width": 0},
            },
            text=df[value],
            texttemplate="%{text:,.0f}",
            textposition="auto",
            hovertemplate=(
                "%{y}: %{x:,.0f}<extra></extra>"
                if horizontal
                else "%{x}: %{y:,.0f}<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        title=title,
        bargap=0.35,
        showlegend=False,
    )

    st.plotly_chart(
        style_chart(fig, height, show_legend=False),
        use_container_width=True,
    )


def donut_chart(
    df: pd.DataFrame,
    category: str,
    value: str,
    title: str,
    *,
    color_map: dict[str, str] | None = None,
) -> None:
    if df.empty:
        st.info("No data available.")
        return

    colors = [
        (
            color_map.get(str(name), BLUE)
            if color_map
            else CHART_COLORS[i % len(CHART_COLORS)]
        )
        for i, name in enumerate(df[category])
    ]

    fig = go.Figure(
        go.Pie(
            labels=df[category],
            values=df[value],
            hole=0.68,
            marker={"colors": colors},
            textinfo="percent",
            textposition="outside",
            hovertemplate=(
                "%{label}<br>"
                "%{value:,.0f} entities<br>"
                "%{percent}<extra></extra>"
            ),
        )
    )

    fig.update_layout(title=title)

    st.plotly_chart(
        style_chart(fig, 350),
        use_container_width=True,
    )


def status_message(
    level: str,
    message: str,
) -> None:
    if level == "critical":
        st.error(message)
    elif level == "warning":
        st.warning(message)
    elif level == "success":
        st.success(message)
    else:
        st.info(message)


def detection_outcome_chart(
    tp: int,
    fp: int,
    fn: int,
    tn: int,
) -> None:
    labels = [
        "Correct Alerts",
        "False Alerts",
        "Missed Positives",
        "Correct Non-alerts",
    ]

    values = [tp, fp, fn, tn]
    colors = [TEAL, AMBER, RED, BLUE]

    fig = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker_color=colors,
            text=values,
            texttemplate="%{text:,}",
            textposition="outside",
            cliponaxis=False,
        )
    )

    fig.update_layout(
        title="Detection Outcome Breakdown",
        showlegend=False,
        yaxis={"autorange": "reversed"},
    )

    st.plotly_chart(
        style_chart(fig, 370, show_legend=False),
        use_container_width=True,
    )
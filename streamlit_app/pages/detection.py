import plotly.graph_objects as go
import streamlit as st

from streamlit_app.db import detection_effectiveness
from streamlit_app.insights import (
    detection_outcome_chart,
    explain,
    section,
)
from streamlit_app.theme import (
    classification_metrics,
    number,
    style_chart,
)

st.title("Detection Performance")
st.caption(
    "Evaluate how the alerting engine performs "
    "against synthetic AML reference labels."
)

df = detection_effectiveness()

if len(df) != 1:
    st.error(
        "Detection reporting view must return exactly one row."
    )
    st.stop()

row = df.iloc[0]

tp = int(row["true_positives"])
fp = int(row["false_positives"])
fn = int(row["false_negatives"])
tn = int(row["true_negatives"])

if min(tp, fp, fn, tn) < 0:
    st.error("Negative confusion-matrix counts detected.")
    st.stop()

total = tp + fp + fn + tn

if total == 0:
    st.error("No evaluation records found.")
    st.stop()

metrics = classification_metrics(tp, fp, fn, tn)

section(
    "Model evaluation scorecard",
    "The most important indicators of alerting performance.",
)

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Precision",
    f"{metrics['precision']:.2%}",
)

c2.metric(
    "Recall",
    f"{metrics['recall']:.2%}",
)

c3.metric(
    "F1 Score",
    f"{metrics['f1']:.2%}",
)

c4.metric(
    "False Positive Rate",
    f"{metrics['false_positive_rate']:.2%}",
)

st.info(
    f"**Business takeaway:** Approximately "
    f"{metrics['precision']:.1%} of alerts matched positive "
    f"synthetic labels, while the rules detected "
    f"{metrics['recall']:.1%} of all positive-labeled "
    f"transactions."
)

left, right = st.columns(2)

with left:
    explain(
        "Precision",
        (
            "Of the transactions that generated alerts, "
            f"{metrics['precision']:.1%} had positive labels."
        ),
        (
            "Lower precision generally creates more "
            "false-positive investigation work."
        ),
        "Review alert quality and rule specificity.",
    )

with right:
    explain(
        "Recall",
        (
            "Of the positive-labeled transactions, "
            f"{metrics['recall']:.1%} generated alerts."
        ),
        (
            "Lower recall indicates more labeled positives "
            "were missed by the detection rules."
        ),
        "Review missed-positive patterns.",
    )

st.divider()

section(
    "Detection outcomes",
    "Understand correct alerts, false alerts and missed positives.",
)

with st.container(border=True):
    detection_outcome_chart(tp, fp, fn, tn)

    explain(
        "Detection Outcomes",
        (
            "Each bar represents one possible combination "
            "of an alert decision and a reference label."
        ),
        (
            "False alerts increase workload, while missed "
            "positives indicate gaps in detection coverage."
        ),
        "Balance detection coverage with alert quality.",
    )

st.divider()

section(
    "Confusion matrix",
    "A direct comparison of predictions and reference labels.",
)

with st.container(border=True):
    fig = go.Figure(
        go.Heatmap(
            z=[
                [tn, fp],
                [fn, tp],
            ],
            x=[
                "No Alert",
                "Alert",
            ],
            y=[
                "Labeled Negative",
                "Labeled Positive",
            ],
            text=[
                [f"{tn:,}", f"{fp:,}"],
                [f"{fn:,}", f"{tp:,}"],
            ],
            texttemplate="%{text}",
            textfont={"size": 17},
            colorscale=[
                [0.0, "#142238"],
                [0.5, "#256B83"],
                [1.0, "#2DD4BF"],
            ],
            showscale=False,
            hovertemplate=(
                "Actual: %{y}<br>"
                "Decision: %{x}<br>"
                "Count: %{z:,}<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        title="Actual Labels vs Alert Decisions",
    )

    fig.update_yaxes(autorange="reversed")

    st.plotly_chart(
        style_chart(fig, 410, show_legend=False),
        use_container_width=True,
    )

st.divider()

section(
    "Evaluation totals",
    "Detailed outcome counts for audit and governance.",
)

c1, c2, c3, c4 = st.columns(4)

c1.metric("Correct Alerts", number(tp))
c2.metric("False Alerts", number(fp))
c3.metric("Missed Positives", number(fn))
c4.metric("Correct Non-alerts", number(tn))

with st.expander("How are these metrics calculated?"):
    st.markdown(
        """
        **Precision** = Correct Alerts / All Alerts

        **Recall** = Correct Alerts / All Positive Labels

        **F1 Score** = Harmonic mean of Precision and Recall

        **False Positive Rate** =
        False Alerts / All Negative Labels

        **Specificity** =
        Correct Non-alerts / All Negative Labels
        """
    )

st.warning(
    "These are offline metrics using synthetic labels. "
    "They do not measure confirmed real-world financial crime."
)
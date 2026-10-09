from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

# ============================================================
# ENTERPRISE DESIGN TOKENS
# ============================================================

BACKGROUND = "#0B1424"
PANEL = "#142238"
BORDER = "#293C54"
TEXT = "#EAF2FC"
MUTED = "#94A8C0"

TEAL = "#2DD4BF"
BLUE = "#60A5FA"
AMBER = "#FBBF24"
RED = "#FB7185"
PURPLE = "#A78BFA"

CHART_COLORS = [
    TEAL,
    BLUE,
    PURPLE,
    AMBER,
    RED,
    "#38BDF8",
    "#34D399",
]

RISK_COLORS = {
    "LOW": TEAL,
    "MEDIUM": BLUE,
    "HIGH": AMBER,
    "CRITICAL": RED,
    "UNKNOWN": MUTED,
}


# ============================================================
# CSS STYLING
# ============================================================

def apply_styles() -> None:
    """
    Load CSS styling without creating custom HTML dashboard
    components. Cards, tables, and charts remain native
    Streamlit and Plotly elements.
    """
    css_path = Path(__file__).with_name("styles.css")

    css = css_path.read_text(encoding="utf-8")

    st.html(f"<style>{css}</style>")


# ============================================================
# PLOTLY CHART THEME
# ============================================================

def style_chart(
    fig: go.Figure,
    height: int = 350,
    *,
    show_legend: bool = True,
) -> go.Figure:
    """
    Apply a consistent enterprise dark theme to Plotly charts.
    """
    fig.update_layout(
        template="plotly_dark",
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={
            "family": "Arial, sans-serif",
            "color": TEXT,
            "size": 12,
        },
        colorway=CHART_COLORS,
        title={
            "font": {
                "size": 16,
                "color": TEXT,
            },
            "x": 0,
            "xanchor": "left",
        },
        margin={
            "l": 12,
            "r": 20,
            "t": 65,
            "b": 30,
        },
        hoverlabel={
            "bgcolor": PANEL,
            "bordercolor": BORDER,
            "font": {
                "color": TEXT,
            },
        },
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.01,
            "xanchor": "right",
            "x": 1,
        },
        showlegend=show_legend,
    )

    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        linecolor=BORDER,
        tickfont={
            "color": MUTED,
        },
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(148,168,192,0.10)",
        zeroline=False,
        tickfont={
            "color": MUTED,
        },
    )

    return fig


# ============================================================
# NUMBER FORMATTING
# ============================================================

def number(value: object) -> str:
    """
    Convert a numeric value to comma-separated text.

    Example:
        number(5078345) -> '5,078,345'
    """
    if value is None:
        return "0"

    if isinstance(value, (int, float, str)):
        try:
            numeric_value = int(float(value))
        except (TypeError, ValueError):
            numeric_value = 0
        return f"{numeric_value:,}"

    return "0"


def compact_number(value: float) -> str:
    """
    Format large values for dashboard KPI cards.

    Examples:
        5078345 -> '5.08M'
        42645   -> '42.6K'
    """
    value = float(value)

    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"

    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"

    return f"{value:,.0f}"


# ============================================================
# MATHEMATICAL HELPERS
# ============================================================

def safe_divide(
    numerator: float,
    denominator: float,
) -> float:
    """
    Safely divide two numbers.

    Returns zero if denominator is zero.
    """
    if denominator == 0:
        return 0.0

    return numerator / denominator


def percentage(
    numerator: float,
    denominator: float,
) -> float:
    """
    Return percentage points.

    Examples:
        percentage(25, 100) -> 25.0
        percentage(5, 0)    -> 0.0
    """
    return safe_divide(
        numerator,
        denominator,
    ) * 100.0


# ============================================================
# AML RISK CLASSIFICATION
# ============================================================

def risk_level(score: int | float) -> str:
    """
    Classify AML risk scores using project thresholds.

    LOW:      0-24
    MEDIUM:  25-49
    HIGH:    50-79
    CRITICAL: 80+

    This classification is a monitoring priority,
    not a probability of financial crime.
    """
    if score >= 80:
        return "CRITICAL"

    if score >= 50:
        return "HIGH"

    if score >= 25:
        return "MEDIUM"

    return "LOW"


# ============================================================
# DETECTION EVALUATION METRICS
# ============================================================

def classification_metrics(
    tp: int,
    fp: int,
    fn: int,
    tn: int,
) -> dict[str, float]:
    """
    Calculate confusion-matrix evaluation metrics.

    TP: True Positives
    FP: False Positives
    FN: False Negatives
    TN: True Negatives

    Metrics are fractions in the range 0-1.
    """
    precision = safe_divide(
        tp,
        tp + fp,
    )

    recall = safe_divide(
        tp,
        tp + fn,
    )

    f1 = safe_divide(
        2 * precision * recall,
        precision + recall,
    )

    specificity = safe_divide(
        tn,
        tn + fp,
    )

    false_positive_rate = safe_divide(
        fp,
        fp + tn,
    )

    accuracy = safe_divide(
        tp + tn,
        tp + fp + fn + tn,
    )

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "specificity": specificity,
        "false_positive_rate": false_positive_rate,
        "accuracy": accuracy,
    }
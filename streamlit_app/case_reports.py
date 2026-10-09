from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from html import escape
from typing import Any, Mapping

import pandas as pd

REPORT_VERSION = "1.0"

ALLOWED_PRIORITIES = {"P1", "P2", "P3", "P4"}

ALLOWED_STATUSES = {
    "OPEN",
    "IN_REVIEW",
    "CLOSED",
}

EXCLUDED_FIELDS = {
    "is_laundering",
    "laundering_label",
    "ground_truth",
    "true_label",
}


def safe_text(value: Any) -> str:
    """Convert a value to HTML-safe text."""
    if value is None:
        return "Not available"

    if isinstance(value, (datetime, date)):
        return escape(value.isoformat())

    if isinstance(value, float) and pd.isna(value):
        return "Not available"

    if isinstance(value, Decimal):
        return escape(format(value, "f"))

    return escape(str(value), quote=True)


def safe_number(value: Any, default: int = 0) -> int:
    """Convert a nullable numeric value to an integer."""
    if value is None or pd.isna(value):
        return default

    return int(value)


def record_value(
    record: Mapping[str, Any],
    field: str,
    default: Any = None,
) -> Any:
    """Read a field without requiring a specific row type."""
    return record.get(field, default)


def html_table(
    rows: list[tuple[str, Any]],
) -> str:
    """Render a two-column HTML table."""
    body = "\n".join(
        (
            "<tr>"
            f"<th scope='row'>{safe_text(label)}</th>"
            f"<td>{safe_text(value)}</td>"
            "</tr>"
        )
        for label, value in rows
    )

    return (
        "<table class='detail-table'>"
        "<tbody>"
        f"{body}"
        "</tbody>"
        "</table>"
    )


def frame_table(
    frame: pd.DataFrame,
    max_rows: int = 100,
) -> str:
    """Render a DataFrame with escaped cell values."""
    if frame.empty:
        return "<p class='muted'>No records available.</p>"

    visible_columns = [
        column
        for column in frame.columns
        if str(column).lower() not in EXCLUDED_FIELDS
    ]

    if not visible_columns:
        return "<p class='muted'>No reportable fields.</p>"

    limited = frame.loc[:, visible_columns].head(max_rows)

    headers = "".join(
        f"<th>{safe_text(column)}</th>"
        for column in visible_columns
    )

    body_rows = []

    for row in limited.itertuples(index=False, name=None):
        cells = "".join(
            f"<td>{safe_text(value)}</td>"
            for value in row
        )

        body_rows.append(f"<tr>{cells}</tr>")

    return (
        "<div class='table-scroll'>"
        "<table>"
        f"<thead><tr>{headers}</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody>"
        "</table>"
        "</div>"
    )


def priority_interpretation(
    tier: str,
) -> str:
    descriptions = {
        "P1": (
            "Highest investigation review priority "
            "under the current heuristic scoring policy."
        ),
        "P2": (
            "Elevated investigation review priority. "
            "Analyst assessment is recommended."
        ),
        "P3": (
            "Moderate investigation review priority. "
            "Review the contributing indicators."
        ),
        "P4": (
            "Lower relative investigation review priority. "
            "The alert remains available for review."
        ),
    }

    return descriptions.get(
        tier,
        "Investigation priority could not be determined.",
    )


def build_case_summary(
    alert: Mapping[str, Any],
    rule_count: int,
) -> str:
    """Produce a neutral, evidence-based summary."""
    alert_id = safe_number(record_value(alert, "alert_id"))
    transaction_id = safe_number(
        record_value(alert, "transaction_id")
    )

    tier = str(
        record_value(alert, "priority_tier", "UNKNOWN")
    )

    priority_score = safe_number(
        record_value(
            alert,
            "investigation_priority_score",
        )
    )

    transaction_risk = safe_number(
        record_value(
            alert,
            "transaction_risk_score",
        )
    )

    return (
        f"Alert {alert_id} concerns transaction "
        f"{transaction_id}. The current investigation "
        f"priority is {tier}, with a heuristic priority "
        f"score of {priority_score}/100 and a transaction "
        f"risk score of {transaction_risk}/100. "
        f"The available evidence contains {rule_count} "
        f"recorded detection rule hit(s). "
        f"{priority_interpretation(tier)} "
        "These indicators support review and do not "
        "establish criminal conduct."
    )


def validate_alert(
    alert: Mapping[str, Any],
) -> None:
    """Reject incomplete or inconsistent case evidence."""
    required_fields = (
        "alert_id",
        "transaction_id",
        "priority_tier",
        "investigation_priority_score",
        "transaction_risk_score",
        "transaction_component",
        "entity_component",
        "dual_high_risk_component",
    )

    missing = [
        field
        for field in required_fields
        if field not in alert
        or alert[field] is None
        or pd.isna(alert[field])
    ]

    if missing:
        raise ValueError(
            "Missing required alert fields: "
            + ", ".join(missing)
        )

    tier = str(alert["priority_tier"])

    if tier not in ALLOWED_PRIORITIES:
        raise ValueError(
            f"Unsupported priority tier: {tier}"
        )

    priority_score = safe_number(
        alert["investigation_priority_score"]
    )

    if not 0 <= priority_score <= 100:
        raise ValueError(
            "Investigation priority score must be "
            "between 0 and 100."
        )

    transaction_risk = safe_number(
        alert["transaction_risk_score"]
    )

    if not 0 <= transaction_risk <= 100:
        raise ValueError(
            "Transaction risk score must be "
            "between 0 and 100."
        )

    components = (
        safe_number(alert["transaction_component"]),
        safe_number(alert["entity_component"]),
        safe_number(
            alert["dual_high_risk_component"]
        ),
    )

    if sum(components) != priority_score:
        raise ValueError(
            "Priority score does not match "
            "its recorded components."
        )

    expected_tier = (
        "P1"
        if priority_score >= 80
        else "P2"
        if priority_score >= 65
        else "P3"
        if priority_score >= 50
        else "P4"
    )

    if tier != expected_tier:
        raise ValueError(
            "Priority tier does not match "
            "the recorded score."
        )


def entity_section(
    title: str,
    entity_key: Any,
    profile: pd.DataFrame,
) -> str:
    fields = [
        "entity_risk_score",
        "entity_risk_level",
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

    if profile.empty:
        details = (
            "<p class='muted'>"
            "Entity profile is unavailable."
            "</p>"
        )
    else:
        record = profile.iloc[0].to_dict()

        details = html_table(
            [
                (
                    field.replace("_", " ").title(),
                    record.get(field),
                )
                for field in fields
                if field in record
            ]
        )

    return (
        "<section>"
        f"<h2>{safe_text(title)}</h2>"
        f"<p><strong>Entity:</strong> "
        f"{safe_text(entity_key)}</p>"
        f"{details}"
        "</section>"
    )


def generate_case_report(
    alert: Mapping[str, Any],
    rules: pd.DataFrame,
    sender_profile: pd.DataFrame,
    receiver_profile: pd.DataFrame,
    generated_at: datetime | None = None,
) -> str:
    """Generate a self-contained, printable HTML report."""
    validate_alert(alert)

    generated = generated_at or datetime.now().astimezone()

    alert_id = safe_number(alert["alert_id"])

    tier = str(alert["priority_tier"])

    status = str(
        record_value(
            alert,
            "alert_status",
            "UNKNOWN",
        )
    )

    if status not in ALLOWED_STATUSES:
        status = "UNKNOWN"

    rule_count = len(rules)

    summary = build_case_summary(
        alert,
        rule_count,
    )

    transaction_fields = [
        ("Alert ID", record_value(alert, "alert_id")),
        (
            "Transaction ID",
            record_value(alert, "transaction_id"),
        ),
        (
            "Transaction timestamp",
            record_value(
                alert,
                "transaction_timestamp",
            ),
        ),
        (
            "Sender entity",
            record_value(
                alert,
                "sender_entity_key",
            ),
        ),
        (
            "Receiver entity",
            record_value(
                alert,
                "receiver_entity_key",
            ),
        ),
        (
            "Amount paid",
            record_value(alert, "amount_paid"),
        ),
        (
            "Payment currency",
            record_value(
                alert,
                "payment_currency_key",
            ),
        ),
        (
            "Cross-currency transaction",
            record_value(
                alert,
                "is_cross_currency",
            ),
        ),
    ]

    scoring_fields = [
        (
            "Investigation priority score",
            alert["investigation_priority_score"],
        ),
        (
            "Transaction risk score",
            alert["transaction_risk_score"],
        ),
        (
            "Transaction component",
            alert["transaction_component"],
        ),
        (
            "Entity component",
            alert["entity_component"],
        ),
        (
            "Dual high-risk component",
            alert["dual_high_risk_component"],
        ),
    ]

    sender_key = record_value(
        alert,
        "sender_entity_key",
    )

    receiver_key = record_value(
        alert,
        "receiver_entity_key",
    )

    css = """
    :root {
        color-scheme: light;
    }

    * {
        box-sizing: border-box;
    }

    body {
        margin: 0;
        background: #f2f5f9;
        color: #142238;
        font-family: Arial, Helvetica, sans-serif;
        line-height: 1.55;
    }

    .document {
        max-width: 1020px;
        margin: 32px auto;
        padding: 44px;
        background: white;
        border: 1px solid #dce3ed;
        border-radius: 14px;
    }

    .eyebrow {
        color: #147d86;
        font-size: 12px;
        font-weight: bold;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }

    h1 {
        font-size: 30px;
        margin: 8px 0;
    }

    h2 {
        font-size: 18px;
        margin-top: 0;
        padding-bottom: 10px;
        border-bottom: 1px solid #e4e9f1;
    }

    .subtitle,
    .muted {
        color: #62718a;
    }

    .meta {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
        margin-top: 20px;
    }

    .pill {
        padding: 7px 13px;
        border-radius: 7px;
        background: #e9f1f8;
        font-size: 13px;
        font-weight: bold;
    }

    section {
        margin-top: 30px;
        break-inside: avoid;
    }

    .summary {
        background: #f3f8fa;
        border-left: 4px solid #147d86;
        padding: 18px;
        border-radius: 5px;
    }

    table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
    }

    th,
    td {
        padding: 10px 12px;
        text-align: left;
        vertical-align: top;
        border-bottom: 1px solid #e5eaf1;
        overflow-wrap: anywhere;
    }

    th {
        background: #f5f7fa;
        font-weight: bold;
    }

    .detail-table th {
        width: 38%;
    }

    .table-scroll {
        overflow-x: auto;
    }

    .warning {
        padding: 16px;
        background: #fff8e9;
        border-left: 4px solid #d79b2a;
    }

    footer {
        margin-top: 36px;
        padding-top: 16px;
        border-top: 1px solid #e4e9f1;
        color: #62718a;
        font-size: 12px;
    }

    @media print {
        body {
            background: white;
        }

        .document {
            margin: 0;
            padding: 10px;
            border: none;
            max-width: none;
        }

        @page {
            size: A4;
            margin: 15mm;
        }
    }
    """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FCI Investigation Report - Alert {alert_id}</title>
<style>{css}</style>
</head>
<body>
<main class="document">

<header>
<div class="eyebrow">FCI / Investigation Intelligence</div>
<h1>Investigation Case Report</h1>
<p class="subtitle">
Financial Crime Intelligence &amp; Banking Risk Command Center
</p>
<div class="meta">
<span class="pill">Alert #{alert_id}</span>
<span class="pill">Priority {safe_text(tier)}</span>
<span class="pill">Status {safe_text(status)}</span>
</div>
<p class="subtitle">
Generated: {safe_text(generated)}
</p>
</header>

<section>
<h2>Executive Case Summary</h2>
<div class="summary">{safe_text(summary)}</div>
</section>

<section>
<h2>Transaction Evidence</h2>
{html_table(transaction_fields)}
</section>

<section>
<h2>Explainable Risk Scoring</h2>
{html_table(scoring_fields)}
<p class="muted">
Priority is a heuristic triage score. It is not a
probability of money laundering or criminal conduct.
</p>
</section>

<section>
<h2>Recorded Detection Rule Hits</h2>
{frame_table(rules)}
</section>

{entity_section("Sender Entity Intelligence", sender_key, sender_profile)}

{entity_section("Receiver Entity Intelligence", receiver_key, receiver_profile)}

<section>
<h2>Methodology and Limitations</h2>
<div class="warning">
<p>
This report is generated from a synthetic AML research
environment and is intended for analytical demonstration.
</p>
<p>
Risk indicators, alert scores, rule hits and entity
relationships are signals for investigation. They do not
establish illicit activity or legal wrongdoing.
</p>
<p>
Transaction amounts are displayed in their recorded
currencies. No cross-currency totals or FX-normalized
exposure estimates are calculated.
</p>
<p>
Rapid movement and related transaction indicators do not
establish direct tracing of funds.
</p>
<p>
This document is a point-in-time export, not an immutable
evidence record or audited case-management decision.
</p>
</div>
</section>

<footer>
FCI Analytics Platform | Report version {REPORT_VERSION}
<br>
Read-only investigation intelligence | Synthetic research data
</footer>

</main>
</body>
</html>"""


def report_filename(alert_id: int) -> str:
    """Create a predictable download filename."""
    return f"FCI_Investigation_Alert_{int(alert_id)}.html"
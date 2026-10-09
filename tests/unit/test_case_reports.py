from datetime import datetime, timezone

import pandas as pd
import pytest

from streamlit_app.case_reports import (
    build_case_summary,
    generate_case_report,
    priority_interpretation,
    report_filename,
    safe_text,
    validate_alert,
)


@pytest.fixture
def sample_alert():
    return {
        "alert_id": 1001,
        "transaction_id": 5001,
        "priority_tier": "P2",
        "investigation_priority_score": 70,
        "transaction_risk_score": 80,
        "transaction_component": 48,
        "entity_component": 22,
        "dual_high_risk_component": 0,
        "alert_status": "OPEN",
        "transaction_timestamp": datetime(
            2025, 1, 1, 12, 30
        ),
        "sender_entity_key": "BANK_A_ACCOUNT_1",
        "receiver_entity_key": "BANK_B_ACCOUNT_2",
        "amount_paid": 12500,
        "payment_currency_key": "USD",
        "is_cross_currency": False,
    }


@pytest.fixture
def sample_rules():
    return pd.DataFrame(
        [
            {
                "rule_code": "TEST_RULE",
                "detected_at": datetime(
                    2025, 1, 1, 12, 31
                ),
            }
        ]
    )


@pytest.fixture
def sample_profile():
    return pd.DataFrame(
        [
            {
                "entity_risk_score": 75,
                "entity_risk_level": "HIGH",
                "active_days": 12,
                "outgoing_transactions": 20,
                "incoming_transactions": 15,
                "velocity_days": 3,
                "fan_in_days": 2,
                "fan_out_days": 1,
                "high_behavior_days": 4,
                "rapid_movement_count": 5,
                "structuring_candidate_days": 1,
            }
        ]
    )


def test_safe_text_escapes_html():
    assert safe_text("<script>") == "&lt;script&gt;"


def test_safe_text_handles_missing_value():
    assert safe_text(None) == "Not available"


def test_priority_interpretation():
    assert "Elevated" in priority_interpretation("P2")


def test_validate_alert_accepts_consistent_score(
    sample_alert,
):
    validate_alert(sample_alert)


def test_validate_alert_rejects_inconsistent_score(
    sample_alert,
):
    sample_alert["investigation_priority_score"] = 90

    with pytest.raises(ValueError):
        validate_alert(sample_alert)


def test_validate_alert_rejects_missing_fields(
    sample_alert,
):
    del sample_alert["transaction_component"]

    with pytest.raises(ValueError):
        validate_alert(sample_alert)


def test_case_summary_is_neutral(
    sample_alert,
):
    summary = build_case_summary(sample_alert, 2)

    assert "Alert 1001" in summary
    assert "do not establish criminal conduct" in summary


def test_report_contains_required_sections(
    sample_alert,
    sample_rules,
    sample_profile,
):
    report = generate_case_report(
        alert=sample_alert,
        rules=sample_rules,
        sender_profile=sample_profile,
        receiver_profile=sample_profile,
        generated_at=datetime(
            2026, 10, 9, 10, 0, tzinfo=timezone.utc
        ),
    )

    assert "Executive Case Summary" in report
    assert "Transaction Evidence" in report
    assert "Explainable Risk Scoring" in report
    assert "Recorded Detection Rule Hits" in report
    assert "Sender Entity Intelligence" in report
    assert "Receiver Entity Intelligence" in report


def test_report_excludes_synthetic_label(
    sample_alert,
    sample_profile,
):
    rules = pd.DataFrame(
        [
            {
                "rule_code": "TEST_RULE",
                "is_laundering": 1,
            }
        ]
    )

    sample_alert["is_laundering"] = 1

    report = generate_case_report(
        alert=sample_alert,
        rules=rules,
        sender_profile=sample_profile,
        receiver_profile=sample_profile,
    )

    assert "is_laundering" not in report


def test_report_escapes_entity_identifier(
    sample_alert,
):
    sample_alert["sender_entity_key"] = (
        "<script>alert('x')</script>"
    )

    report = generate_case_report(
        alert=sample_alert,
        rules=pd.DataFrame(),
        sender_profile=pd.DataFrame(),
        receiver_profile=pd.DataFrame(),
    )

    assert "<script>alert('x')</script>" not in report
    assert "&lt;script&gt;" in report


def test_report_filename():
    assert (
        report_filename(1001)
        == "FCI_Investigation_Alert_1001.html"
    )
import pytest

from src.risk.scoring import (
    ALERT_SQL,
    HITS_SQL,
    SCORE_SQL,
    build_risk_scores,
)


@pytest.mark.parametrize("batch_size", [0, -1, -100])
def test_rejects_invalid_batch_size(batch_size):
    with pytest.raises(ValueError, match="batch_size must be positive"):
        build_risk_scores("postgresql://unused", batch_size=batch_size)


def test_scoring_uses_no_aml_label():
    assert "is_laundering" not in SCORE_SQL.lower()
    assert "is_laundering" not in HITS_SQL.lower()


def test_scoring_has_all_four_rules():
    for rule in (
        "HIGH_VALUE",
        "CROSS_CURRENCY",
        "CROSS_BANK",
        "DUPLICATE",
    ):
        assert rule in SCORE_SQL
        assert rule in HITS_SQL


def test_scoring_has_idempotent_upsert():
    assert "ON CONFLICT (transaction_id) DO UPDATE" in SCORE_SQL


def test_rule_hits_prevent_duplicates():
    assert "ON CONFLICT (transaction_id, rule_code) DO NOTHING" in HITS_SQL


def test_alerts_only_for_high_risk():
    assert "risk_level IN ('HIGH', 'CRITICAL')" in ALERT_SQL


def test_alerts_preserve_review_status():
    assert "alert_status" not in ALERT_SQL.lower()

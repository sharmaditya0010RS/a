import pytest

from streamlit_app.theme import (
    classification_metrics,
    percentage,
    risk_level,
)


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0, "LOW"),
        (24, "LOW"),
        (25, "MEDIUM"),
        (49, "MEDIUM"),
        (50, "HIGH"),
        (79, "HIGH"),
        (80, "CRITICAL"),
        (100, "CRITICAL"),
    ],
)
def test_risk_level(score: int, expected: str) -> None:
    assert risk_level(score) == expected


def test_percentage_zero_denominator() -> None:
    assert percentage(5, 0) == 0.0


def test_perfect_detection() -> None:
    result = classification_metrics(
        tp=100,
        fp=0,
        fn=0,
        tn=900,
    )

    assert result["precision"] == 1.0
    assert result["recall"] == 1.0
    assert result["f1"] == 1.0
    assert result["false_positive_rate"] == 0.0


def test_no_alerts() -> None:
    result = classification_metrics(
        tp=0,
        fp=0,
        fn=10,
        tn=90,
    )

    assert result["precision"] == 0.0
    assert result["recall"] == 0.0
    assert result["f1"] == 0.0


def test_known_detection_metrics() -> None:
    result = classification_metrics(
        tp=80,
        fp=20,
        fn=20,
        tn=880,
    )

    assert result["precision"] == pytest.approx(0.8)
    assert result["recall"] == pytest.approx(0.8)
    assert result["f1"] == pytest.approx(0.8)
    assert result["specificity"] == pytest.approx(
        880 / 900
    )


def test_accuracy() -> None:
    result = classification_metrics(
        tp=50,
        fp=10,
        fn=20,
        tn=920,
    )

    assert result["accuracy"] == pytest.approx(0.97)
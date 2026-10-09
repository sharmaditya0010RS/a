import pytest


def calculate_priority(
    transaction_score: int,
    sender_score: int,
    receiver_score: int,
    sender_level: str,
    receiver_level: str,
) -> tuple[int, str]:
    transaction_component = round(
        min(max(transaction_score, 0), 100) * 0.60
    )

    entity_component = round(
        min(
            max(sender_score, receiver_score, 0),
            100,
        ) * 0.30
    )

    dual_high_risk_component = (
        10
        if sender_level in {"HIGH", "CRITICAL"}
        and receiver_level in {"HIGH", "CRITICAL"}
        else 0
    )

    score = min(
        100,
        transaction_component
        + entity_component
        + dual_high_risk_component,
    )

    if score >= 80:
        tier = "P1"
    elif score >= 65:
        tier = "P2"
    elif score >= 50:
        tier = "P3"
    else:
        tier = "P4"

    return score, tier


@pytest.mark.parametrize(
    (
        "transaction_score",
        "sender_score",
        "receiver_score",
        "sender_level",
        "receiver_level",
        "expected",
    ),
    [
        (100, 100, 100, "HIGH", "HIGH", (100, "P1")),
        (100, 50, 0, "HIGH", "LOW", (75, "P2")),
        (80, 40, 20, "MEDIUM", "LOW", (60, "P3")),
        (50, 0, 0, "LOW", "LOW", (30, "P4")),
        (0, 0, 0, "LOW", "LOW", (0, "P4")),
    ],
)
def test_priority_examples(
    transaction_score,
    sender_score,
    receiver_score,
    sender_level,
    receiver_level,
    expected,
):
    assert calculate_priority(
        transaction_score,
        sender_score,
        receiver_score,
        sender_level,
        receiver_level,
    ) == expected


def test_priority_is_bounded():
    score, tier = calculate_priority(
        500,
        500,
        500,
        "CRITICAL",
        "CRITICAL",
    )

    assert score == 100
    assert tier == "P1"


def test_dual_risk_bonus_requires_both_entities():
    one_high = calculate_priority(
        60, 80, 10, "HIGH", "LOW"
    )

    both_high = calculate_priority(
        60, 80, 80, "HIGH", "HIGH"
    )

    assert both_high[0] - one_high[0] == 10
from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from sqlalchemy import text

from streamlit_app.case_reports import (
    generate_case_report,
    report_filename,
)
from streamlit_app.investigation_db import (
    alert_evidence,
    entity_profile,
    investigation_engine,
    triggered_rules,
)

OUTPUT_DIR = Path("reports") / "investigations"


def main() -> None:
    engine = investigation_engine()

    with engine.connect() as connection:
        alert_id = connection.execute(
            text(
                """
                SELECT alert_id
                FROM investigation.vw_prioritized_alerts
                WHERE priority_tier = 'P2'
                ORDER BY
                    investigation_priority_score DESC,
                    alert_id
                LIMIT 1
                """
            )
        ).scalar_one_or_none()

    if alert_id is None:
        raise RuntimeError(
            "No P2 alert is available for report validation."
        )

    evidence = alert_evidence(int(alert_id))

    if evidence.empty:
        raise RuntimeError(
            "Alert evidence query returned no rows."
        )

    alert = cast(dict[str, Any], evidence.iloc[0].to_dict())

    rules = triggered_rules(
        int(alert["transaction_id"])
    )

    sender_profile = entity_profile(
        str(alert["sender_entity_key"])
    )

    receiver_profile = entity_profile(
        str(alert["receiver_entity_key"])
    )

    html_report = generate_case_report(
        alert=alert,
        rules=rules,
        sender_profile=sender_profile,
        receiver_profile=receiver_profile,
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        OUTPUT_DIR / report_filename(int(alert_id))
    )

    output_path.write_text(
        html_report,
        encoding="utf-8",
    )

    print("PHASE 9 CASE REPORT VALIDATION")
    print("=" * 42)
    print(f"Alert ID: {alert_id}")
    print(f"Priority: {alert['priority_tier']}")
    print(f"Rule hits: {len(rules)}")
    print(f"Report: {output_path.resolve()}")
    print("CASE REPORT GENERATED SUCCESSFULLY")


if __name__ == "__main__":
    main()
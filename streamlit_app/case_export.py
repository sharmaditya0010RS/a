from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import streamlit as st

from streamlit_app.case_reports import (
    generate_case_report,
    report_filename,
)
from streamlit_app.investigation_db import (
    alert_evidence,
    entity_profile,
    triggered_rules,
)


def render_case_export(alert_id: int) -> None:
    """Render a read-only case report export section."""
    st.subheader("Investigation Case Report")

    st.caption(
        "Generate an analyst-ready report using the selected "
        "alert's recorded evidence, rule hits and entity profiles."
    )

    st.info(
        "Reports contain synthetic research data and are not "
        "formal regulatory filings or findings of wrongdoing."
    )

    if not st.button(
        "Prepare investigation report",
        key=f"prepare_case_report_{alert_id}",
        use_container_width=True,
        type="primary",
    ):
        return

    try:
        with st.spinner("Collecting investigation evidence..."):
            evidence = alert_evidence(int(alert_id))

            if evidence.empty:
                st.error("Selected alert evidence was not found.")
                return

            alert_raw = evidence.iloc[0].to_dict()
            alert: dict[str, Any] = {
                str(key): value for key, value in alert_raw.items()
            }

            transaction_id = int(alert["transaction_id"])

            rules = triggered_rules(transaction_id)

            sender = str(alert["sender_entity_key"])
            receiver = str(alert["receiver_entity_key"])

            sender_profile = entity_profile(sender)
            receiver_profile = entity_profile(receiver)

            report_html = generate_case_report(
                alert=alert,
                rules=rules,
                sender_profile=sender_profile,
                receiver_profile=receiver_profile,
                generated_at=datetime.now(timezone.utc),
            )

            st.session_state["prepared_case_report"] = {
                "alert_id": int(alert_id),
                "html": report_html,
            }

    except Exception as exc:
        st.error("Case report generation failed.")
        st.exception(exc)
        return

    st.success("Investigation report prepared successfully.")


def render_prepared_download(alert_id: int) -> None:
    """Display a download only for the currently selected alert."""
    prepared = st.session_state.get("prepared_case_report")

    if not prepared:
        return

    if prepared["alert_id"] != int(alert_id):
        return

    st.download_button(
        label="Download investigation report (HTML)",
        data=prepared["html"].encode("utf-8"),
        file_name=report_filename(int(alert_id)),
        mime="text/html",
        use_container_width=True,
        key=f"download_case_report_{alert_id}",
    )

    st.caption(
        "Open the downloaded HTML in a browser and use "
        "Print > Save as PDF if a PDF copy is needed."
    )


def case_export_section(alert_id: int) -> None:
    """Complete report export section for an investigation page."""
    with st.container(border=True):
        render_case_export(alert_id)
        render_prepared_download(alert_id)
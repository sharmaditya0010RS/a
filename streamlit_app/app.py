from __future__ import annotations

import streamlit as st

from streamlit_app.db import health_check
from streamlit_app.theme import apply_styles

# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="FCI | Financial Crime Command Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_styles()


# ============================================================
# SIDEBAR BRANDING AND SYSTEM STATUS
# ============================================================

with st.sidebar:
    st.markdown("## FCI COMMAND")

    st.caption(
        "FINANCIAL CRIME INTELLIGENCE"
    )

    st.divider()

    st.markdown("**SYSTEM STATUS**")

    try:
        database_connected = health_check()
    except Exception:
        database_connected = False

    if database_connected:
        st.success("PostgreSQL - Connected")
    else:
        st.error("PostgreSQL - Disconnected")

        st.info(
            "Start the PostgreSQL Docker container "
            "and verify your database configuration."
        )

        st.stop()

    st.caption(
        "Source: PostgreSQL analytical warehouse"
    )

    st.caption(
        "Environment: Synthetic AML research"
    )

    st.caption(
        "Access: Read-only dashboard"
    )

    st.divider()

    if st.button(
        "Refresh dashboard data",
        use_container_width=True,
        type="primary",
    ):
        st.cache_data.clear()
        st.rerun()

    st.divider()

    st.markdown("**PLATFORM MODULES**")

    st.caption(
        "Monitoring | Investigations | "
        "Entity Intelligence | Governance"
    )

    st.divider()

    st.caption(
        "FCI ANALYTICS PLATFORM"
    )

    st.caption(
        "Portfolio research environment"
    )

    st.caption(
        "Not a production financial-crime "
        "decision system"
    )


# ============================================================
# ENTERPRISE MULTIPAGE NAVIGATION
# ============================================================

pages = {
    "COMMAND CENTER": [
        st.Page(
            "pages/executive.py",
            title="Executive Overview",
            icon="📊",
            default=True,
        ),
    ],
    "INVESTIGATIONS": [
        st.Page(
            "pages/investigations.py",
            title="Alert Investigation",
            icon="🚨",
        ),
        st.Page(
            "pages/workbench.py",
            title="Advanced Investigation",
            icon="🔎",
        ),
    ],
    "ENTITY INTELLIGENCE": [
        st.Page(
            "pages/entities.py",
            title="Entity Risk Intelligence",
            icon="🌐",
        ),
    ],
    "GOVERNANCE & CONTROL": [
        st.Page(
            "pages/detection.py",
            title="Detection Performance",
            icon="📈",
        ),
        st.Page(
            "pages/operations.py",
            title="Data Quality & Operations",
            icon="🗃️",
        ),
    ],
}


# ============================================================
# RUN SELECTED PAGE
# ============================================================

navigation = st.navigation(
    pages,
    position="sidebar",
)

navigation.run()

import streamlit as st

from src.common.config import get_settings
from src.common.database import check_database_connection

st.set_page_config(
    page_title="Financial Crime Intelligence",
    page_icon="🏦",
    layout="wide",
)

settings = get_settings()

st.title("Global Financial Crime Intelligence")
st.subheader("Enterprise Banking Risk Command Center")

st.caption(f"Environment: {settings.app_env}")
st.caption(f"Platform Version: {settings.app_version}")

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Platform", "Initialized")

with col2:
    st.metric("Pipeline", "Not Started")

with col3:
    try:
        healthy = check_database_connection()
        st.metric("Database", "Connected" if healthy else "Disconnected")
    except Exception:
        st.metric("Database", "Disconnected")

st.info("Phase 0: Infrastructure and environment initialization")

import pandas as pd
import streamlit as st

from streamlit_app.db import (
    operational_counts,
    validation_snapshot,
)
from streamlit_app.insights import (
    bar_chart,
    explain,
    section,
)
from streamlit_app.theme import (
    compact_number,
    number,
)

st.title("Data Quality & Operations")
st.caption(
    "Monitor data coverage, reconciliation controls "
    "and analytical pipeline completeness."
)

snapshot = validation_snapshot()

if len(snapshot) != 1:
    st.error("Data validation snapshot is unavailable.")
    st.stop()

row = snapshot.iloc[0]

facts = int(row["facts"])
scores = int(row["scores"])
alerts = int(row["alerts"])
activity = int(row["activity"])
signals = int(row["signals"])
advanced = int(row["advanced"])
entities = int(row["entities"])
profiles = int(row["profiles"])

checks = {
    "Transaction scoring coverage": facts == scores,
    "Daily signal coverage": activity == signals,
    "Advanced behaviour coverage": activity == advanced,
    "Entity profile coverage": entities == profiles,
    "Alert count within transaction count": alerts <= facts,
}

passed = sum(checks.values())
total = len(checks)

section(
    "Platform health scorecard",
    "Reconciliation checks for the current PostgreSQL datasets.",
)

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Controls Passed",
    f"{passed}/{total}",
)

c2.metric(
    "Warehouse Transactions",
    compact_number(facts),
)

c3.metric(
    "Scored Transactions",
    compact_number(scores),
)

c4.metric(
    "Entity Risk Profiles",
    compact_number(profiles),
)

if passed == total:
    st.success(
        "All displayed count-reconciliation controls passed."
    )
else:
    st.error(
        f"{total - passed} reconciliation control(s) failed."
    )

st.divider()

section(
    "Data quality controls",
    "Identify any mismatches between analytical processing stages.",
)

results = pd.DataFrame(
    [
        {
            "Control": name,
            "Status": "PASS" if result else "FAIL",
        }
        for name, result in checks.items()
    ]
)

st.dataframe(
    results,
    use_container_width=True,
    hide_index=True,
)

st.divider()

section(
    "Pipeline volume monitoring",
    "Understand the number of records produced at each stage.",
)

counts = operational_counts()

with st.container(border=True):
    bar_chart(
        counts,
        "dataset",
        "row_count",
        "Records by Analytical Dataset",
        horizontal=True,
        height=440,
    )

    explain(
        "Pipeline Record Volumes",
        (
            "The chart shows how many rows exist in "
            "each major analytical dataset."
        ),
        (
            "Different datasets naturally have different "
            "row counts. Daily behaviour records, for example, "
            "are not expected to equal unique entity counts."
        ),
        (
            "Investigate only mismatches between datasets "
            "that are expected to reconcile."
        ),
    )

with st.expander("View exact dataset counts"):
    st.dataframe(
        counts,
        use_container_width=True,
        hide_index=True,
    )

st.divider()

section(
    "Governance explanations",
    "What each important quality control means.",
)

left, right = st.columns(2)

with left:
    explain(
        "Transaction Scoring Coverage",
        (
            f"{number(scores)} score records exist "
            f"for {number(facts)} warehouse transactions."
        ),
        (
            "Every transaction should receive a "
            "monitoring score."
        ),
        "Investigate missing or duplicate score records.",
    )

with right:
    explain(
        "Entity Profile Coverage",
        (
            f"{number(profiles)} entity profiles exist "
            f"for {number(entities)} dimension entities."
        ),
        (
            "Every entity should be represented in "
            "the entity risk intelligence layer."
        ),
        "Review missing profiles and entity mappings.",
    )

st.info(
    "These controls validate aggregate row-count relationships. "
    "Passing them does not prove one-to-one key coverage, "
    "freshness or complete data accuracy."
)
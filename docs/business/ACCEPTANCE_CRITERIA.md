
# Acceptance Criteria and Requirements Traceability

Document ID: FCI-UAT-001
Version: 1.0

## 1. Phase 1 Acceptance Criteria

| ID | Acceptance Criterion | Verification |
|---|---|---|
| AC-001 | BRD exists with business scope and objectives | Document review |
| AC-002 | FRD contains uniquely identified capabilities | Document review |
| AC-003 | Stakeholder personas and workflows are documented | Document review |
| AC-004 | AML use cases specify inputs, logic, outputs, and limitations | Document review |
| AC-005 | KPI dictionary defines units and calculation rules | Document review |
| AC-006 | Data assumptions distinguish verified and unverified facts | Document review |
| AC-007 | Business requirements map to functional capabilities | Traceability review |
| AC-008 | Synthetic data limitations are explicit | Document review |
| AC-009 | Phase 1 files are committed to Git | Git validation |
| AC-010 | Phase 0 regression tests remain green | Automated tests |

## 2. Business-to-Functional Traceability

| Business Requirement | Functional Requirements | Planned Verification |
|---|---|---|
| BR-001 | FR-001, FR-002, FR-005 | Ingestion tests |
| BR-002 | FR-003, FR-004 | Lineage and rerun tests |
| BR-003 | FR-013, FR-016, FR-027 | SQL and KPI reconciliation |
| BR-004 | FR-014, FR-028 | Time-series validation |
| BR-005 | FR-015, FR-031 | Entity aggregation tests |
| BR-006 | FR-019, FR-020, FR-021 | Rule unit tests |
| BR-007 | FR-023, FR-024 | Risk score explanation tests |
| BR-008 | FR-025, FR-026 | Label separation tests |
| BR-009 | FR-007 through FR-012 | Data quality tests |
| BR-010 | FR-027 through FR-033 | Dashboard UAT |
| BR-011 | FR-034 through FR-037 | Excel MIS validation |
| BR-012 | FR-043, FR-044 | Orchestration tests |
| BR-013 | FR-045, FR-046 | CI validation |
| BR-014 | FR-017, FR-042 | Documentation review |
| BR-015 | FR-023, FR-038 through FR-041 | Simulated workflow UAT |
| BR-016 | FR-031, FR-042 | Dimension availability review |

## 3. Project-Wide Acceptance Scenarios

### UAT-001 — Reproducible Ingestion

Given a valid source file and initialized database,
when ingestion is executed,
then row accounting must reconcile and processing metadata must be recorded.

### UAT-002 — Safe Rerun

Given an already processed source file,
when the ingestion process is rerun,
then unintended duplicate transaction records must not be created.

### UAT-003 — Data Quality Failure

Given a source record violating an approved critical rule,
when validation executes,
then the failure must be recorded and handled according to the configured policy.

### UAT-004 — KPI Reconciliation

Given the same reporting period and filters,
when a KPI is calculated in SQL, Power BI, Excel, and Streamlit,
then outputs must agree within documented numeric precision.

### UAT-005 — Monitoring Rule Explainability

Given a transaction that triggers a configured rule,
when its indicator is inspected,
then the rule identifier, parameter values, and relevant evidence must be available.

### UAT-006 — Synthetic Label Separation

Given a source AML label and a generated monitoring indicator,
when reporting is produced,
then both must be represented as distinct fields and concepts.

### UAT-007 — Currency Integrity

Given transactions in different currencies,
when transaction value is aggregated,
then values must remain separated by currency unless validated conversion is applied.

### UAT-008 — Operational Metric Integrity

Given no investigation case-management records,
when management reporting is generated,
then case closure and regulatory filing metrics must be unavailable rather than fabricated.

### UAT-009 — Pipeline Failure Visibility

Given a processing task failure,
when pipeline status is inspected,
then the failure and relevant diagnostic details must be visible.

### UAT-010 — Reproducible Environment

Given the documented setup and dependencies,
when a supported environment is initialized,
then the documented tests and health checks must execute successfully.

## 4. Evidence Requirements

Implementation phases must produce relevant evidence, including:

- Automated test results.
- Source profiling reports.
- SQL reconciliation queries.
- Data quality results.
- Model documentation.
- Dashboard screenshots.
- Excel workbook validation.
- Pipeline execution logs.
- Git commit history.

## 5. Phase Exit Decision

Phase 1 is accepted when all Phase 1 acceptance criteria pass and the documentation baseline is committed.

Project-wide UAT scenarios remain pending until their corresponding implementation phases.

## 6. Approval Status

Proposed portfolio baseline. No external business approval is claimed.

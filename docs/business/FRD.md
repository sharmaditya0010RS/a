
# Functional Requirements Document

Document ID: FCI-FRD-001
Version: 1.0
Status: Proposed baseline

## 1. Purpose

Define the functional capabilities required to implement the Global Financial Crime Intelligence & Banking Risk Command Center.

## 2. Functional Architecture

The planned processing flow is:

Synthetic Source Data
→ Source Profiling
→ Ingestion
→ Raw PostgreSQL Layer
→ Quality Validation
→ Analytical Transformations
→ Risk Indicators
→ KPI Models
→ Power BI / Excel / Streamlit

Each transformation must preserve traceability to its input records or documented aggregations.

## 3. Functional Requirements

### Data Ingestion

FR-001: The system shall ingest the selected synthetic transaction CSV.

FR-002: The system shall support configurable chunk sizes.

FR-003: The system shall record ingestion start time, end time, status, and row counts.

FR-004: The system shall prevent unintended duplicate ingestion on repeated execution.

FR-005: The system shall preserve source fields before applying analytical transformations.

FR-006: The system shall reject or quarantine structurally invalid records according to documented rules.

### Data Quality

FR-007: The system shall profile column types, missing values, distinct counts, and value distributions.

FR-008: The system shall evaluate required-field completeness.

FR-009: The system shall evaluate duplicate records using a documented business key or source-aware fallback.

FR-010: The system shall validate numeric and temporal fields.

FR-011: The system shall report quality results by processing run.

FR-012: The system shall identify reconciliation differences between source, accepted, and rejected records.

### Analytical Warehouse

FR-013: The system shall provide reusable analytical models.

FR-014: The system shall support transaction analysis by date and time.

FR-015: The system shall support sender and receiver activity analysis.

FR-016: The system shall expose transaction amount measures without mixing incompatible currencies.

FR-017: The system shall document grain, keys, and lineage for each published model.

FR-018: The system shall implement automated model tests.

### Financial Crime Indicators

FR-019: The system shall detect configurable high-value transaction indicators.

FR-020: The system shall detect configurable transaction velocity indicators.

FR-021: The system shall identify repeated transfers between counterparties.

FR-022: The system shall support behavioral concentration indicators.

FR-023: The system shall generate an explainable risk score from documented features.

FR-024: The system shall retain rule identifiers and triggering evidence.

FR-025: The system shall distinguish generated monitoring indicators from source-provided AML labels.

FR-026: The system shall evaluate monitoring indicators against available labels only where semantically appropriate.

### Business Intelligence

FR-027: The system shall provide an executive transaction monitoring overview.

FR-028: The system shall provide time-series transaction trends.

FR-029: The system shall provide transaction amount and volume distributions.

FR-030: The system shall provide risk indicator and risk score summaries.

FR-031: The system shall support filtering by valid source dimensions.

FR-032: The system shall show data freshness and reporting scope.

FR-033: The system shall reconcile displayed KPIs with approved SQL definitions.

### Management Information Reporting

FR-034: The system shall generate an Excel MIS workbook.

FR-035: The workbook shall include reporting metadata and KPI summaries.

FR-036: The workbook shall include risk monitoring and data quality summaries.

FR-037: The workbook shall identify unavailable metrics rather than inventing values.

### Streamlit Command Center

FR-038: The system shall provide a functional Streamlit interface.

FR-039: The interface shall display database and pipeline health.

FR-040: The interface shall expose relevant analytical KPIs.

FR-041: The interface shall support selected filters and drill-down views.

FR-042: The interface shall clearly identify synthetic data and derived indicators.

### Automation and Controls

FR-043: The system shall support scheduled pipeline orchestration.

FR-044: The system shall log task success and failure.

FR-045: The system shall execute automated unit and integration tests.

FR-046: The system shall execute linting and validation in CI.

FR-047: The system shall externalize environment-specific configuration.

FR-048: The system shall document reproducible local startup and validation commands.

## 4. Reporting Conventions

- Transaction count uses the documented fact-table grain.
- Monetary values are reported in original currency unless a validated conversion process exists.
- A flagged transaction is not a confirmed crime.
- A generated alert is not a filed regulatory report.
- A synthetic AML label is not an actual investigator disposition.
- Missing operational data must appear as unavailable, not zero.

## 5. Error Handling

The system shall expose actionable failures for:

- Missing source files.
- Invalid configuration.
- Database connection failure.
- Invalid source schema.
- Reconciliation failure.
- Data quality rule failure.
- Transformation failure.
- Export failure.

Failures must not be silently converted into successful processing results.

## 6. Functional Acceptance

A functional requirement is accepted only when:

1. The capability is implemented.
2. Its expected behavior is documented.
3. Relevant automated or manual tests pass.
4. Data lineage and metric interpretation are clear.
5. Known limitations are recorded.

## 7. Approval Status

This is a proposed functional specification for a synthetic portfolio project.

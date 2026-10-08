
# Business Requirements Document

## Global Financial Crime Intelligence & Banking Risk Command Center

Document ID: FCI-BRD-001
Version: 1.0
Status: Proposed baseline
Project type: Enterprise analytics portfolio
Business domain: Anti-Money Laundering and Financial Crime Intelligence

## 1. Executive Summary

The Global Financial Crime Intelligence & Banking Risk Command Center is a simulated enterprise analytics platform designed to help a multinational bank understand transaction activity, identify potentially suspicious patterns, prioritize risk, and communicate financial crime intelligence to operational and executive stakeholders.

The platform will combine reproducible data ingestion, PostgreSQL analytics, data quality controls, dimensional modeling, risk indicators, business intelligence dashboards, Excel management reporting, and a Streamlit command center.

The project uses synthetic transaction data. Its results demonstrate analytical capabilities and do not represent actual financial crime findings or regulatory decisions.

## 2. Business Problem

Financial crime monitoring teams face challenges when transaction data, monitoring outputs, investigation records, and management reports are distributed across disconnected systems.

This creates difficulties in:

- Obtaining a consistent view of transaction activity.
- Identifying unusual transaction behavior.
- Understanding risk concentrations.
- Explaining monitoring outcomes to management.
- Reproducing regulatory and internal reporting metrics.
- Tracking data quality and processing reliability.
- Distinguishing genuine risk signals from data limitations.

## 3. Business Objectives

| ID | Objective | Proposed Success Measure |
|---|---|---|
| BO-01 | Establish a reliable transaction intelligence foundation | Reproducible ingestion with auditable run records |
| BO-02 | Improve transaction monitoring visibility | Standardized transaction and risk dashboards |
| BO-03 | Identify suspicious behavioral indicators | Documented and testable detection rules |
| BO-04 | Support risk-based prioritization | Explainable transaction or entity risk scores |
| BO-05 | Improve management reporting | Reconciled KPI definitions across outputs |
| BO-06 | Strengthen data governance | Automated quality checks and exception reporting |
| BO-07 | Support repeatable operations | Scheduled processing, tests, and CI checks |

These measures are project acceptance targets, not claims of realized banking benefits.

## 4. Business Scope

### In Scope

- Synthetic AML transaction data ingestion.
- Source profiling and schema validation.
- Data cleansing and quality monitoring.
- PostgreSQL analytical storage.
- SQL and dbt transformation models.
- Transaction-level and entity-level analytical metrics.
- Explainable rule-based risk indicators.
- AML typology-inspired analytical use cases.
- Power BI operational and executive dashboards.
- Excel management information reporting.
- Streamlit command center.
- Automated workflows and software quality controls.
- Documentation and traceability.

### Out of Scope

- Live banking system integration.
- Real customer personal information.
- Production sanctions screening.
- Actual suspicious activity report submission.
- Real regulatory filing.
- Automated customer account blocking.
- Production case management.
- Claims that a synthetic AML label proves criminal conduct.
- Deployment into a regulated production environment.

## 5. Stakeholders

| Stakeholder | Primary Need |
|---|---|
| Chief Compliance Officer | Executive risk visibility |
| MLRO / BSA Officer | Monitoring governance and escalation visibility |
| AML Operations Manager | Workload and risk prioritization |
| AML Investigator | Explainable indicators and transaction context |
| Financial Crime Intelligence Analyst | Behavioral patterns and risk concentrations |
| Data Engineer | Reliable pipelines and data quality |
| Analytics Engineer | Trusted models and metric consistency |
| BI Analyst | Actionable dashboards and reporting |
| Model Risk / Validation Reviewer | Reproducibility, limitations, and testing |
| Internal Audit | Traceability and evidence |

## 6. Business Requirements

| ID | Requirement | Priority |
|---|---|---|
| BR-001 | Consolidate source transactions into a trusted analytical store | Must |
| BR-002 | Preserve source lineage and ingestion history | Must |
| BR-003 | Report transaction counts and monetary values | Must |
| BR-004 | Analyze transaction activity over time | Must |
| BR-005 | Analyze sender and receiver activity | Must |
| BR-006 | Surface high-value and unusual transaction patterns | Must |
| BR-007 | Provide explainable risk indicators | Must |
| BR-008 | Distinguish source AML labels from generated risk alerts | Must |
| BR-009 | Monitor data quality and reconciliation | Must |
| BR-010 | Provide interactive management dashboards | Must |
| BR-011 | Produce reproducible Excel MIS outputs | Should |
| BR-012 | Support scheduled pipeline execution | Should |
| BR-013 | Provide automated validation and CI checks | Must |
| BR-014 | Document data limitations and interpretation boundaries | Must |
| BR-015 | Support simulated investigation prioritization | Should |
| BR-016 | Support geographical analysis only where source data supports it | Must |

## 7. Business Decisions Supported

The platform should help stakeholders decide:

1. Which transaction patterns require closer examination.
2. Which accounts or entities demonstrate concentrated monitoring indicators.
3. Which payment corridors or activity categories merit additional review, where supported by available fields.
4. Whether transaction activity or risk indicators are changing over time.
5. Whether data is complete and reliable enough for reporting.
6. Which analytical rules generate the greatest simulated monitoring workload.

The platform does not independently determine guilt, legal violations, or regulatory filing obligations.

## 8. Operating Principles

- Evidence before interpretation.
- Reproducible metrics.
- Explainable detection logic.
- Explicit source-to-report lineage.
- Clear separation of observed facts and derived indicators.
- No fabricated investigation outcomes.
- No fabricated customer attributes.
- No unsupported geographical enrichment.
- Privacy-conscious handling of identifiers.
- Human review for any consequential decision.

## 9. Nonfunctional Requirements

| ID | Requirement |
|---|---|
| NFR-001 | All pipeline stages must be repeatable |
| NFR-002 | Processing failures must be logged |
| NFR-003 | Data quality failures must be measurable |
| NFR-004 | Database credentials must remain outside Git |
| NFR-005 | Automated tests must run without manual editing |
| NFR-006 | Dashboard metrics must reconcile with SQL outputs |
| NFR-007 | Analytical assumptions must be documented |
| NFR-008 | Large source files must support chunk-based ingestion |
| NFR-009 | Transformations must avoid unintended duplicate counting |
| NFR-010 | Outputs must clearly identify synthetic or simulated data |

## 10. Key Dependencies

- IBM AML synthetic dataset acquisition and profiling.
- Python 3.12 environment.
- PostgreSQL 16 analytical database.
- Stable transaction schema.
- Documented metric and risk rule definitions.
- Power BI and Excel availability for reporting.
- Docker availability for local database execution.

## 11. Principal Risks

| Risk | Mitigation |
|---|---|
| Source schema differs from expectations | Profile before designing physical models |
| Duplicate or malformed transactions | Define source-aware validation rules |
| AML labels are misinterpreted | Document label meaning and limitations |
| Risk indicators produce false positives | Use explainable logic and measured evaluation |
| Missing geography | Restrict analysis to supported attributes |
| Large file causes memory pressure | Use streaming and chunked processing |
| KPI definitions diverge | Maintain a shared KPI dictionary |
| Pipeline reruns duplicate data | Design idempotent ingestion |

## 12. Success Criteria

Phase 1 is complete when all business requirements are documented, prioritized, traceable to functional capabilities, and supported by measurable acceptance criteria.

Project-wide success will be assessed during later implementation and user acceptance testing.

## 13. Approval Status

This document is a portfolio simulation baseline.

No actual banking stakeholder has approved these requirements.

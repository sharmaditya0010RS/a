
# Stakeholders and Operational Workflows

Document ID: FCI-OPS-001
Version: 1.0

## 1. Stakeholder Personas

### Chief Compliance Officer

Needs a concise view of financial crime exposure, material changes, monitoring coverage, and data reliability.

Primary outputs:
- Executive dashboard.
- Period-over-period monitoring trends.
- Risk concentration summaries.
- Governance exceptions.

### MLRO / BSA Officer

Needs visibility into monitoring indicators, potential escalation patterns, and reporting limitations.

Primary outputs:
- Monitoring rule summaries.
- High-priority indicators.
- Explainable risk evidence.
- Audit-ready metric definitions.

### AML Operations Manager

Needs insight into monitoring volume and simulated alert prioritization.

Primary outputs:
- Indicator volumes.
- Rule contribution analysis.
- Prioritized review queues.
- Workload scenarios.

### AML Investigator

Needs transaction context and explanations for why activity was flagged.

Primary outputs:
- Transaction drill-down.
- Counterparty activity.
- Rule evidence.
- Risk score components.

### Financial Crime Intelligence Analyst

Needs to explore behavioral patterns and emerging concentrations.

Primary outputs:
- Temporal patterns.
- Network-inspired counterparty analysis.
- Activity segmentation.
- Rule performance evaluation.

### Data Engineering and Analytics Teams

Need reliable ingestion, models, lineage, tests, and reproducible execution.

Primary outputs:
- Processing logs.
- Data quality results.
- Warehouse documentation.
- CI validation results.

### Internal Audit and Model Validation

Need evidence of consistent controls, explainable methodology, and acknowledged limitations.

Primary outputs:
- Requirement traceability.
- Test results.
- Rule definitions.
- Data assumptions.
- Version history.

## 2. Workflow A — Transaction Monitoring

1. Source transaction file becomes available.
2. Ingestion validates source structure.
3. Accepted records enter the analytical database.
4. Data quality checks evaluate reliability.
5. Warehouse transformations prepare transaction features.
6. Monitoring rules evaluate transactions and activity windows.
7. Indicators are stored with evidence and rule identifiers.
8. Dashboards summarize patterns and concentrations.
9. Analysts review selected results in the simulated workflow.

Output: explainable monitoring indicators.

## 3. Workflow B — Risk Prioritization

1. Select eligible transactions or entities.
2. Calculate approved behavioral features.
3. Apply documented scoring rules.
4. Store score, version, and contributing features.
5. Assign analytical priority bands.
6. Display prioritization and supporting evidence.

Output: simulated risk prioritization.

No automated enforcement action is authorized.

## 4. Workflow C — Executive Reporting

1. Confirm reporting period.
2. Validate processing completeness.
3. Calculate approved KPI definitions.
4. Reconcile totals across SQL and reporting outputs.
5. Generate dashboard and Excel MIS.
6. Record refresh time and known limitations.
7. Present findings with appropriate caveats.

Output: reproducible management information.

## 5. Workflow D — Data Quality Exception

1. Execute validation checks.
2. Record failed checks and affected records.
3. Classify severity.
4. Prevent publication when a critical control fails.
5. Correct source mapping or transformation logic.
6. Rerun processing.
7. Preserve exception and resolution evidence.

Output: auditable data quality status.

## 6. Responsibility Matrix

| Activity | Responsible | Accountable |
|---|---|---|
| Business requirements | Business Analyst | Compliance Sponsor |
| Source ingestion | Data Engineer | Data Engineering Lead |
| Data quality rules | Data Engineer | Data Owner |
| Warehouse models | Analytics Engineer | Analytics Lead |
| AML indicator definitions | Financial Crime Analyst | AML Operations Lead |
| Risk score validation | Model Validation Reviewer | Model Risk Owner |
| Dashboard design | BI Analyst | Business Product Owner |
| MIS reporting | BI Analyst | Reporting Owner |
| CI and orchestration | Data Engineer | Engineering Lead |
| User acceptance testing | Business Analyst | Business Product Owner |

All roles are fictional project personas.

## 7. Operational Boundaries

The project does not include live investigators, actual regulatory reporting, or real customer decision-making.

Where investigation workflow metrics are required, the project must use explicitly labeled simulation data or mark those metrics unavailable.

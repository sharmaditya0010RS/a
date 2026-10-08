
# AML Monitoring Use-Case Catalog

Document ID: FCI-AML-001
Version: 1.0

## 1. Purpose

Define explainable transaction-monitoring use cases for synthetic financial crime analytics.

These are analytical indicators, not proof of money laundering.

Thresholds and observation windows will be selected after source profiling. No numerical threshold in this document is represented as a validated regulatory standard.

## 2. Use Cases

### UC-001 — High-Value Transaction Indicator

Business question:
Which transactions exceed a documented monitoring threshold?

Inputs:
- Transaction amount.
- Transaction currency.
- Transaction timestamp.
- Transaction identifier or source-derived key.

Logic:
Compare eligible transactions with a configurable threshold defined in the same currency or within a validated normalization framework.

Output:
- Flag status.
- Threshold.
- Observed amount.
- Rule version.

Limitations:
High-value activity may be legitimate. Cross-currency comparison requires validated conversion.

### UC-002 — Transaction Velocity

Business question:
Which accounts demonstrate unusually frequent activity over a defined interval?

Inputs:
- Account identifier.
- Transaction timestamp.
- Transaction direction.

Logic:
Count eligible transactions per account within a configurable rolling time window.

Output:
- Transaction count.
- Window boundaries.
- Trigger status.

Limitations:
Requires reliable timestamps and stable account identifiers.

### UC-003 — Repeated Counterparty Transfers

Business question:
Which sender-receiver relationships exhibit concentrated repeated activity?

Inputs:
- Sender identifier.
- Receiver identifier.
- Transaction timestamp.
- Amount.

Logic:
Aggregate repeated transfers by counterparty pair over a defined period.

Output:
- Pair-level transaction count.
- Total reported amount by currency.
- Monitoring indicator.

Limitations:
Repeated transfers can reflect normal commercial relationships.

### UC-004 — Rapid Movement of Funds

Business question:
Do accounts receive and subsequently send funds within a short interval?

Inputs:
- Account identifier.
- Incoming transaction timestamp.
- Outgoing transaction timestamp.
- Amount and currency.

Logic:
Identify time-ordered incoming and outgoing activity within a configurable window.

Output:
- Account.
- Related transaction references.
- Time difference.
- Amount context.

Limitations:
Matching transfers does not establish beneficial ownership or criminal intent.

### UC-005 — Activity Concentration

Business question:
Does a small set of accounts or counterparties account for a disproportionate share of activity?

Inputs:
- Account or counterparty identifier.
- Transaction amount.
- Transaction count.
- Currency.

Logic:
Calculate concentration measures and compare them with documented analytical benchmarks.

Output:
- Concentration ratio.
- Ranking.
- Segment context.

Limitations:
Concentration may be expected for business or settlement accounts.

### UC-006 — Potential Structuring Pattern

Business question:
Are there repeated transactions clustered below a configured monitoring threshold?

Inputs:
- Account identifier.
- Transaction amount.
- Currency.
- Transaction timestamp.

Logic:
Identify repeated transactions within a defined amount band and observation window.

Output:
- Transaction group.
- Count.
- Amount distribution.
- Triggering rule.

Limitations:
A threshold-proximity pattern alone is insufficient to infer intent.

### UC-007 — Synthetic Label Evaluation

Business question:
How do generated monitoring indicators compare with source-provided AML labels?

Inputs:
- Source AML label, where available.
- Generated indicator.
- Evaluation population.

Logic:
Construct a documented comparison with explicit label semantics, coverage, and denominator definitions.

Output:
- Confusion matrix.
- Precision.
- Recall.
- False-positive rate.
- Evaluation limitations.

Limitations:
Synthetic labels are dataset annotations, not verified criminal outcomes. Metrics must not be described as real-world model effectiveness.

## 3. Use-Case Priority

| Use Case | Priority | Planned Phase |
|---|---|---|
| UC-001 | Must | Risk Scoring |
| UC-002 | Must | Risk Scoring |
| UC-003 | Must | Risk Scoring |
| UC-004 | Should | Risk Scoring |
| UC-005 | Must | EDA / Risk Scoring |
| UC-006 | Should | Risk Scoring |
| UC-007 | Must | Validation |

## 4. Implementation Controls

Every implemented rule must have:

- Stable rule identifier.
- Business description.
- Required input fields.
- Eligibility conditions.
- Configurable parameters.
- Version.
- Triggering evidence.
- Unit tests.
- Known limitations.

## 5. Interpretation Standard

Use the term "monitoring indicator" for generated analytical flags.

Use the term "source AML label" for dataset annotations.

Use the term "simulated alert" only when an explicit simulation process creates alert records.

Do not call any of these a confirmed suspicious activity report or criminal finding.

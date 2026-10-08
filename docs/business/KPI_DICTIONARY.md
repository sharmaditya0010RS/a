
# Financial Crime KPI Dictionary

Document ID: FCI-KPI-001
Version: 1.0

## 1. Purpose

Provide a single source of truth for the analytical metrics displayed in SQL, Power BI, Excel MIS, and Streamlit.

Definitions are provisional until the source schema and transaction grain are verified.

## 2. Transaction KPIs

### KPI-001 — Total Transactions

Definition:
Count of accepted transaction records at the approved transaction grain.

Calculation:
COUNT(*) over the approved transaction fact population.

Unit:
Transactions.

### KPI-002 — Total Transaction Value

Definition:
Sum of eligible transaction amounts within a single reporting currency.

Calculation:
SUM(transaction_amount) grouped by currency.

Unit:
Original transaction currency.

Restriction:
Do not sum amounts across different currencies without validated conversion.

### KPI-003 — Average Transaction Value

Definition:
Arithmetic mean of eligible transaction amounts within a currency.

Calculation:
SUM(transaction_amount) / COUNT(eligible transactions).

Unit:
Original transaction currency.

### KPI-004 — Unique Sending Accounts

Definition:
Distinct sending account identifiers in the approved transaction population.

Calculation:
COUNT(DISTINCT sender_account_id).

Unit:
Accounts.

### KPI-005 — Unique Receiving Accounts

Definition:
Distinct receiving account identifiers in the approved transaction population.

Calculation:
COUNT(DISTINCT receiver_account_id).

Unit:
Accounts.

### KPI-006 — Daily Transaction Count

Definition:
Count of accepted transactions grouped by approved transaction date.

Unit:
Transactions per day.

### KPI-007 — Daily Transaction Value

Definition:
Sum of accepted transaction amounts by transaction date and currency.

Unit:
Currency units per day.

## 3. Financial Crime Monitoring KPIs

### KPI-008 — Source AML-Labeled Transactions

Definition:
Count of transactions marked with the dataset's AML label, subject to confirmed label semantics.

Unit:
Transactions.

Restriction:
This is not a count of confirmed financial crimes.

### KPI-009 — Source AML Label Rate

Definition:
Source AML-labeled transactions divided by eligible labeled transactions.

Calculation:
AML-labeled transaction count / eligible labeled transaction count.

Unit:
Percentage.

### KPI-010 — Generated Monitoring Indicators

Definition:
Number of transaction-rule trigger events.

Unit:
Rule triggers.

Restriction:
One transaction may trigger multiple rules.

### KPI-011 — Distinct Flagged Transactions

Definition:
Number of distinct eligible transactions triggering at least one monitoring rule.

Unit:
Transactions.

### KPI-012 — Monitoring Flag Rate

Definition:
Distinct flagged transactions divided by eligible evaluated transactions.

Unit:
Percentage.

### KPI-013 — High-Risk Transactions

Definition:
Distinct transactions classified in the highest risk band by the approved scoring configuration.

Unit:
Transactions.

### KPI-014 — High-Risk Transaction Rate

Definition:
High-risk transactions divided by eligible scored transactions.

Unit:
Percentage.

### KPI-015 — Average Risk Score

Definition:
Mean score across the eligible scored population.

Unit:
Score points.

Restriction:
Requires a documented scoring scale and version.

## 4. Data Quality KPIs

### KPI-016 — Source Row Count

Definition:
Number of rows read from the source dataset.

Unit:
Rows.

### KPI-017 — Accepted Row Count

Definition:
Number of rows successfully accepted into the approved raw or staging layer.

Unit:
Rows.

### KPI-018 — Rejected Row Count

Definition:
Number of source rows rejected under documented validation rules.

Unit:
Rows.

### KPI-019 — Row Reconciliation Difference

Definition:
Source row count minus accepted row count minus rejected row count, where the ingestion contract classifies every source row exactly once.

Expected value:
Zero.

### KPI-020 — Required-Field Completeness

Definition:
Percentage of eligible rows with a valid nonmissing value in a required field.

Unit:
Percentage.

### KPI-021 — Duplicate Record Rate

Definition:
Number of duplicate records under the approved duplicate definition divided by eligible records.

Unit:
Percentage.

### KPI-022 — Successful Pipeline Run Rate

Definition:
Successful completed pipeline runs divided by eligible completed pipeline runs.

Unit:
Percentage.

## 5. Conditional Operational KPIs

The following require genuine case-management data or explicitly documented simulation records:

- Alerts assigned to investigators.
- Open investigation cases.
- Average investigation handling time.
- Escalation rate.
- Regulatory report filing rate.
- Analyst productivity.

These metrics must not be populated using transaction counts or AML labels as substitutes.

## 6. Shared KPI Rules

- Every KPI must identify its source model.
- Every KPI must identify its reporting grain.
- Every KPI must define its denominator.
- Every KPI must specify null handling.
- Every KPI must specify currency handling when relevant.
- Every KPI must identify refresh timing.
- Every KPI must reconcile across reporting tools.
- Undefined metrics must display as unavailable rather than zero.
- Percentages must handle zero denominators explicitly.
- Changes in definitions must be version controlled.

## 7. Reporting Dimensions

Candidate dimensions include:

- Transaction date.
- Transaction time.
- Currency.
- Sending account.
- Receiving account.
- Payment or transaction type.
- Source AML label.
- Monitoring rule.
- Risk band.

Final dimensions depend on source profiling and modeled availability.

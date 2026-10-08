
# Data Assumptions, Constraints and Limitations

Document ID: FCI-DATA-001
Version: 1.0

## 1. Source Context

The planned primary source is the IBM AML synthetic transaction dataset.

The configured candidate file is:

data/raw/HI-Small_Trans.csv

The actual dataset file, schema, column names, record counts, data types, date range, and label distribution must be verified during source profiling.

No unverified source statistics are approved for reporting.

## 2. Source Assumptions

| ID | Assumption | Validation |
|---|---|---|
| DA-001 | The source contains transaction-level records | Inspect schema and row grain |
| DA-002 | Transaction amounts are available | Validate columns and types |
| DA-003 | Transaction timestamps are available | Validate parseability |
| DA-004 | Sender and receiver identifiers are available | Inspect source fields |
| DA-005 | Currency attributes may be available | Confirm schema |
| DA-006 | A synthetic AML label may be available | Confirm label semantics |
| DA-007 | Source rows may not contain unique transaction IDs | Establish defensible row identity |
| DA-008 | Geography may be absent or incomplete | Confirm before geographical reporting |

## 3. Dataset Limitations

### Synthetic Data

The source is generated for research and demonstration.

Observed patterns may not represent actual banking customer behavior, production alert distributions, or regulatory risk.

### Ground Truth

An AML label in a synthetic dataset is a dataset annotation.

It is not equivalent to an investigator conclusion, criminal conviction, or regulatory filing.

### Missing Operational Data

The dataset is not assumed to contain:

- Investigation assignment records.
- Case closure timestamps.
- Analyst handling times.
- Regulatory filing decisions.
- Customer due diligence outcomes.
- Verified beneficial ownership relationships.

Such metrics cannot be inferred directly from transaction records.

### Currency

Different currency amounts are not directly additive.

Any consolidated monetary value requires an explicitly defined conversion process and valid exchange-rate data.

### Geography

Location, country, and corridor analysis may be published only when supported by verified source fields or defensible enrichment.

### Identity

Account identifiers are analytical entities.

They are not automatically equivalent to unique customers or legal entities.

### Time

Transaction timestamps require profiling for format, precision, ordering, and timezone interpretation.

A timezone must not be invented where none is supplied.

## 4. Data Quality Rules to Define After Profiling

- Required fields.
- Numeric validity.
- Timestamp validity.
- Amount sign conventions.
- Duplicate identity.
- Currency validity.
- Sender and receiver identity completeness.
- Accepted and rejected row accounting.
- Source-to-target reconciliation.

## 5. Reporting Restrictions

The platform must not:

- Present generated flags as confirmed money laundering.
- Present synthetic labels as regulatory outcomes.
- Fabricate geographical attributes.
- Invent missing customer demographics.
- Sum incompatible currencies.
- Report simulated cases as actual investigations.
- Claim real-world detection effectiveness from synthetic evaluation alone.

## 6. Source Profiling Exit Criteria

Before finalizing the physical data model:

1. Source file identity is recorded.
2. Source file checksum is recorded.
3. Columns and data types are documented.
4. Record count is established.
5. Missing values are measured.
6. Duplicate behavior is analyzed.
7. Monetary fields and currencies are understood.
8. Timestamp coverage is documented.
9. AML label semantics and distribution are inspected.
10. Any changes to provisional requirements are recorded.

## 7. Change Control

If profiling contradicts a source assumption, the affected requirements, KPI definitions, and use cases must be revised before implementation.

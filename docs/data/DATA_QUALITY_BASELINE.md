# Data Quality Baseline — IBM AML HI-Small

## 1. Dataset Identification

| Attribute | Verified value |
|---|---|
| Dataset | HI-Small_Trans.csv |
| Source | IBM AML synthetic transactions |
| Total source rows | 5,078,345 |
| Source columns | 11 |
| SHA-256 | `b19d39f515523373f991b689c07e11e7b0b95c17a2c27a87d91584ae16c5b040` |
| Earliest transaction timestamp | 2022-09-01 00:00:00 |
| Latest transaction timestamp | 2022-09-18 16:18:00 |
| Timestamp timezone | Unknown |

## 2. Source Completeness and Validity

| Check | Observed result |
|---|---|
| Missing values | 0 across all 11 fields under empty-string profiling rules |
| Invalid timestamps | 0 |
| Invalid received amounts | 0 |
| Invalid paid amounts | 0 |
| Negative amounts | 0 |
| Zero amounts | 0 |
| Duplicate SHA-256 row fingerprint candidates | 9 |
| Unique row fingerprints | 5,078,336 |

The duplicate finding is fingerprint-based and does not establish that repeated transactions are invalid.

## 3. AML Label Distribution

| Source label | Transactions |
|---|---:|
| 0 | 5,073,168 |
| 1 | 5,177 |
| Total | 5,078,345 |

The positive-label rate is approximately 0.102%.

The labels are synthetic source annotations. They must not be described as confirmed criminal activity or real-world investigation outcomes.

## 4. Payment Format Distribution

| Payment format | Transactions |
|---|---:|
| ACH | 600,797 |
| Bitcoin | 146,091 |
| Cash | 490,891 |
| Cheque | 1,864,331 |
| Credit Card | 1,323,324 |
| Reinvestment | 481,056 |
| Wire | 171,855 |

## 5. Currency Handling

The source contains 15 distinct receiving currencies and 15 distinct payment currencies.

Received and paid amounts must retain their respective currency identifiers.

Amounts denominated in different currencies must not be aggregated into a single monetary total without an explicit conversion methodology, exchange-rate source, and valuation date.

Bitcoin must not be treated as equivalent to a fiat currency.

## 6. Identifier Handling

`From Bank` and `To Bank` are identifiers and must be stored as text to preserve leading zeros.

The first source `Account` column represents the sending account.

The second source `Account` column, displayed by pandas as `Account.1`, represents the receiving account.

Account identifiers must remain strings.

## 7. Transaction Relationship Findings

| Relationship | Observed transactions |
|---|---:|
| Same sending and receiving bank | 691,255 |
| Same sending and receiving bank and account | 591,212 |

These are descriptive source relationships, not standalone evidence of suspicious activity.

## 8. Raw-Layer Ingestion Policy

1. Preserve all 5,078,345 source records during initial ingestion.
2. Assign each imported row a stable source-row identifier.
3. Preserve source bank and account identifiers without numeric conversion.
4. Preserve both monetary amounts and their original currencies.
5. Preserve the source AML label separately from derived alert and risk-scoring fields.
6. Record ingestion batch identity and source file checksum.
7. Make repeated ingestion of the same source batch idempotent.
8. Flag duplicate fingerprint candidates for investigation rather than automatically deleting them.
9. Preserve source timestamps without inventing a timezone.
10. Reject or quarantine malformed rows in future ingestion batches and report their counts.

## 9. Initial Data Quality Acceptance Criteria

| Control | Acceptance rule |
|---|---|
| Row reconciliation | Raw-layer count equals source count |
| Column reconciliation | All 11 source fields mapped |
| Required identifiers | No unexpected null or blank identifiers |
| Timestamp parsing | All source timestamps parse successfully |
| Amount validity | No invalid decimal values |
| Currency preservation | Both currency fields retained |
| Label validity | Source labels restricted to 0 and 1 |
| Ingestion idempotency | Reprocessing the same batch does not increase row count |
| Duplicate transparency | Repeated fingerprints counted and reported |
| Auditability | Source checksum, batch ID, and ingestion metadata retained |

## 10. Known Limitations

- The dataset is synthetic and does not establish real-world financial crime rates.
- Timestamp timezone is not supplied.
- The source does not provide a guaranteed unique transaction identifier.
- Repeated row fingerprints are not sufficient grounds for deleting transactions.
- Monetary values cannot be meaningfully combined across currencies without conversion.
- The source profile's type inference is provisional.
- Model performance on synthetic labels does not establish real-world operational effectiveness.

## 11. Phase 2 Evidence

- `reports/profiling/dataset_profile.json`
- `reports/profiling/source_audit.json`
- `docs/data/PROFILING_REPORT.md`
- `docs/data/DATA_DICTIONARY.md`
- `tests/unit/test_dataset_profiler.py`
- `tests/unit/test_source_audit.py`

The baseline reflects the completed source audit and will be used as the reconciliation reference for Phase 3 ingestion.
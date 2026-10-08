# Staging and Data Quality Framework

## Objective

Create an analysis-ready PostgreSQL staging layer from the completed IBM AML raw transaction ingestion.

## Source

- Database table: `raw.transactions`
- Expected source records: 5,078,345
- Expected AML-positive synthetic labels: 5,177
- Expected duplicate fingerprint candidates: 9

## Transformation Principles

1. Raw transactions remain immutable.
2. Staging retains one row for every completed raw transaction.
3. Bank and account identifiers remain text.
4. Transaction timestamps retain their source-local, timezone-unspecified interpretation.
5. Received and paid amounts retain their original currencies and decimal precision.
6. Sender and receiver entity keys use length-prefixed bank/account combinations.
7. Same-bank, same-account, and cross-currency indicators are calculated without changing the source.
8. Duplicate fingerprints are flagged, not removed.
9. Data quality failures block publication of a new staging build.

## Quality Controls

- Raw-to-staging row count reconciliation
- AML-positive label reconciliation
- Duplicate candidate reconciliation
- Transaction date consistency
- Same-account/same-bank logical consistency
- Entity key completeness
- Positive monetary amounts
- Valid binary AML labels
- Quality exception count

## Execution

```powershell
venv\Scripts\python.exe -m scripts.build_staging
venv\Scripts\python.exe -m scripts.validate_staging
```

## Failure Handling

The staging replacement and its quality checks are transactional. A failed build must not publish a partially transformed dataset.

Inspect `staging.build_runs` for build status and error messages. Resolve the underlying SQL or source issue before retrying.

## Known Limitations

The duplicate flag identifies repeated source fingerprints, not independently confirmed duplicate financial events.

Currency differences do not automatically imply a suspicious transaction. They describe the source's payment and receiving currencies.

The source AML label is synthetic ground truth for portfolio evaluation and is not an actual regulatory suspicious activity determination.

## Acceptance Criteria

- 5,078,345 staging records
- 5,177 AML-positive labels
- 9 duplicate fingerprint candidates
- Zero failed data quality checks
- Zero unhandled quality issues
- PostgreSQL COPY compatibility test passes
- Complete test suite and Ruff pass
- Phase 4 Git checkpoint committed
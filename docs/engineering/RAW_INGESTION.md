# PostgreSQL Raw Ingestion Runbook

## Objective

Load the IBM AML HI-Small source dataset into PostgreSQL without losing original transaction records, leading-zero identifiers, monetary precision, or source AML labels.

## Source Baseline

- Source file: `data/raw/HI-Small_Trans.csv`
- Expected records: 5,078,345
- Expected AML-positive records: 5,177
- Duplicate row fingerprint candidates: 9
- Expected earliest timestamp: 2022-09-01 00:00:00
- Expected latest timestamp: 2022-09-18 16:18:00

## Database Objects

- `raw.ingestion_batches`: Source file checksum, ingestion status, expected and loaded counts.
- `raw.transactions`: One row per source record, including source row number, source fields, SHA-256 fingerprint, and ingestion timestamp.

## Execution

Run from the project root with the Python virtual environment active.

```powershell
venv\Scripts\python.exe -m scripts.ingest_raw --input data/raw/HI-Small_Trans.csv --chunk-size 50000
```

## Reconciliation

```powershell
venv\Scripts\python.exe -m scripts.reconcile_raw
```

## Idempotency

A completed source checksum must not be ingested again. Re-executing the loader should return `already_loaded` and must not increase the transaction count.

## Failure Handling

If a batch fails, do not delete rows manually and do not blindly restart the loader.

Inspect the batch status, error message, and loaded row count first. Recovery requires a controlled reset or an explicitly implemented resume strategy.

## Data Integrity Rules

- Preserve bank and account identifiers as text.
- Preserve the original transaction timestamp without assigning an unverified timezone.
- Store monetary amounts using PostgreSQL NUMERIC.
- Preserve received and paid currency separately.
- Preserve source AML labels as synthetic annotations.
- Preserve repeated source rows.
- Do not combine monetary values across currencies without a documented conversion methodology.

## Completion Criteria

- Source count equals database count.
- AML-positive count equals 5,177.
- Timestamp boundaries match the source audit.
- Source file checksum matches the profiled file.
- A second ingestion attempt does not add rows.
- Automated tests and lint checks pass.
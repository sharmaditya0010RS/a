# Dataset Profiling Report

Dataset: `HI-Small_Trans.csv`

Rows: 5,078,345

Columns: 11

File size: 475,664,283 bytes

SHA-256: `b19d39f515523373f991b689c07e11e7b0b95c17a2c27a87d91584ae16c5b040`

Profiled at UTC: 2026-10-08T16:30:16.258941+00:00

## Field Completeness

| Field | Inferred Type | Missing | Missing % |
|---|---|---:|---:|
| Timestamp | datetime_candidate | 0 | 0.0000 |
| From Bank | integer_candidate | 0 | 0.0000 |
| Account | string | 0 | 0.0000 |
| To Bank | integer_candidate | 0 | 0.0000 |
| Account.1 | string | 0 | 0.0000 |
| Amount Received | decimal_candidate | 0 | 0.0000 |
| Receiving Currency | string | 0 | 0.0000 |
| Amount Paid | decimal_candidate | 0 | 0.0000 |
| Payment Currency | string | 0 | 0.0000 |
| Payment Format | string | 0 | 0.0000 |
| Is Laundering | integer_candidate | 0 | 0.0000 |

## Profiling Limitations

- All columns were read as strings to preserve source values.
- Type inference is provisional and not a database schema.
- Distinct counts are capped samples, not exact cardinalities.
- Empty strings are treated as missing.
- Duplicate rows have not yet been measured.
- Timestamp parsing does not establish source timezone.
- No AML label semantics are assumed.

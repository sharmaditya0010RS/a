# Dataset Data Dictionary

Source-derived preliminary dictionary.

Business definitions require separate validation.

| Source Field | Inferred Type | Nonempty Rows | Example Values |
|---|---|---:|---|
| Timestamp | datetime_candidate | 5,078,345 | 2022/09/01 00:00, 2022/09/01 00:01, 2022/09/01 00:02 |
| From Bank | integer_candidate | 5,078,345 | 001, 0010057, 0010060 |
| Account | string | 5,078,345 | 100428660, 800042CB0, 800042E70 |
| To Bank | integer_candidate | 5,078,345 | 001, 0010, 0010057 |
| Account.1 | string | 5,078,345 | 800042E70, 800043990, 800043C00 |
| Amount Received | decimal_candidate | 5,078,345 | 0.01, 0.016891, 0.02 |
| Receiving Currency | string | 5,078,345 | Australian Dollar, Bitcoin, Brazil Real |
| Amount Paid | decimal_candidate | 5,078,345 | 0.01, 0.016891, 0.02 |
| Payment Currency | string | 5,078,345 | Australian Dollar, Bitcoin, Brazil Real |
| Payment Format | string | 5,078,345 | ACH, Bitcoin, Cash |
| Is Laundering | integer_candidate | 5,078,345 | 0, 1 |

## Interpretation

Inferred types are candidates only.

Field descriptions, keys, monetary semantics, and AML label interpretation remain subject to review.

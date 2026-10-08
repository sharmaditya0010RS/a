TRUNCATE TABLE staging.transactions;

INSERT INTO staging.transactions (
    transaction_id,
    batch_id,
    source_row_number,
    transaction_timestamp,
    transaction_date,
    transaction_hour,
    from_bank,
    from_account,
    to_bank,
    to_account,
    sender_entity_key,
    receiver_entity_key,
    amount_received,
    receiving_currency,
    amount_paid,
    payment_currency,
    payment_format,
    is_laundering,
    row_sha256,
    is_same_bank,
    is_same_account,
    is_cross_currency,
    is_duplicate_candidate,
    has_quality_issue,
    quality_issue_codes
)
WITH ranked AS (
    SELECT
        r.*,
        ROW_NUMBER() OVER (
            PARTITION BY r.batch_id, r.row_sha256
            ORDER BY r.source_row_number
        ) AS fingerprint_occurrence
    FROM raw.transactions r
    JOIN raw.ingestion_batches b
        ON b.batch_id = r.batch_id
    WHERE b.status = 'completed'
),
prepared AS (
    SELECT
        r.*,
        (
            LENGTH(r.from_bank)::TEXT || ':' || r.from_bank ||
            LENGTH(r.from_account)::TEXT || ':' || r.from_account
        ) AS computed_sender_key,
        (
            LENGTH(r.to_bank)::TEXT || ':' || r.to_bank ||
            LENGTH(r.to_account)::TEXT || ':' || r.to_account
        ) AS computed_receiver_key,
        (r.from_bank = r.to_bank) AS computed_same_bank,
        (
            r.from_bank = r.to_bank
            AND r.from_account = r.to_account
        ) AS computed_same_account,
        (
            r.receiving_currency <> r.payment_currency
        ) AS computed_cross_currency,
        (r.fingerprint_occurrence > 1) AS computed_duplicate,
        ARRAY_REMOVE(
            ARRAY[
                CASE
                    WHEN BTRIM(r.from_bank) = ''
                    THEN 'EMPTY_FROM_BANK'
                END,
                CASE
                    WHEN BTRIM(r.from_account) = ''
                    THEN 'EMPTY_FROM_ACCOUNT'
                END,
                CASE
                    WHEN BTRIM(r.to_bank) = ''
                    THEN 'EMPTY_TO_BANK'
                END,
                CASE
                    WHEN BTRIM(r.to_account) = ''
                    THEN 'EMPTY_TO_ACCOUNT'
                END,
                CASE
                    WHEN r.amount_received <= 0
                    THEN 'INVALID_RECEIVED_AMOUNT'
                END,
                CASE
                    WHEN r.amount_paid <= 0
                    THEN 'INVALID_PAID_AMOUNT'
                END,
                CASE
                    WHEN BTRIM(r.receiving_currency) = ''
                    THEN 'EMPTY_RECEIVING_CURRENCY'
                END,
                CASE
                    WHEN BTRIM(r.payment_currency) = ''
                    THEN 'EMPTY_PAYMENT_CURRENCY'
                END,
                CASE
                    WHEN BTRIM(r.payment_format) = ''
                    THEN 'EMPTY_PAYMENT_FORMAT'
                END
            ],
            NULL
        ) AS computed_issue_codes
    FROM ranked r
)
SELECT
    transaction_id,
    batch_id,
    source_row_number,
    transaction_timestamp,
    transaction_timestamp::DATE,
    EXTRACT(HOUR FROM transaction_timestamp)::SMALLINT,
    from_bank,
    from_account,
    to_bank,
    to_account,
    computed_sender_key,
    computed_receiver_key,
    amount_received,
    receiving_currency,
    amount_paid,
    payment_currency,
    payment_format,
    is_laundering,
    row_sha256,
    computed_same_bank,
    computed_same_account,
    computed_cross_currency,
    computed_duplicate,
    CARDINALITY(computed_issue_codes) > 0,
    computed_issue_codes
FROM prepared;
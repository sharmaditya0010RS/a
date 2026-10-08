DELETE FROM staging.quality_results;

WITH metrics AS (
    SELECT
        (SELECT COUNT(*) FROM raw.transactions r
         JOIN raw.ingestion_batches b ON b.batch_id = r.batch_id
         WHERE b.status = 'completed') AS raw_rows,
        (SELECT COUNT(*) FROM staging.transactions) AS staged_rows,
        (SELECT COUNT(*) FROM staging.transactions
         WHERE is_laundering = 1) AS positive_labels,
        (SELECT COUNT(*) FROM staging.transactions
         WHERE is_duplicate_candidate) AS duplicate_candidates,
        (SELECT COUNT(*) FROM staging.transactions
         WHERE has_quality_issue) AS quality_issue_rows,
        (SELECT COUNT(*) FROM staging.transactions
         WHERE transaction_date <> transaction_timestamp::DATE)
            AS incorrect_dates,
        (SELECT COUNT(*) FROM staging.transactions
         WHERE is_same_account AND NOT is_same_bank)
            AS invalid_same_account_flags,
        (SELECT COUNT(*) FROM staging.transactions
         WHERE sender_entity_key IS NULL
            OR receiver_entity_key IS NULL)
            AS missing_entity_keys,
        (SELECT COUNT(*) FROM staging.transactions
         WHERE amount_received <= 0 OR amount_paid <= 0)
            AS invalid_amounts,
        (SELECT COUNT(*) FROM staging.transactions
         WHERE is_laundering NOT IN (0, 1))
            AS invalid_labels
)
INSERT INTO staging.quality_results (
    check_name,
    observed_value,
    expected_value,
    status
)
SELECT
    checks.check_name,
    checks.observed_value,
    checks.expected_value,
    CASE
        WHEN checks.observed_value = checks.expected_value
        THEN 'PASS'
        ELSE 'FAIL'
    END
FROM metrics
CROSS JOIN LATERAL (
    VALUES
        ('row_count_reconciliation', staged_rows, raw_rows),
        ('aml_positive_count', positive_labels, 5177::BIGINT),
        ('duplicate_candidates', duplicate_candidates, 9::BIGINT),
        ('invalid_transaction_dates', incorrect_dates, 0::BIGINT),
        ('invalid_same_account_flags', invalid_same_account_flags, 0::BIGINT),
        ('missing_entity_keys', missing_entity_keys, 0::BIGINT),
        ('invalid_amounts', invalid_amounts, 0::BIGINT),
        ('invalid_labels', invalid_labels, 0::BIGINT),
        ('quality_issue_rows', quality_issue_rows, 0::BIGINT)
) AS checks(check_name, observed_value, expected_value);
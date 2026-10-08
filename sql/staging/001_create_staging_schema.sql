CREATE SCHEMA IF NOT EXISTS staging;

CREATE TABLE IF NOT EXISTS staging.transactions (
    transaction_id BIGINT PRIMARY KEY,
    batch_id UUID NOT NULL,
    source_row_number BIGINT NOT NULL,
    transaction_timestamp TIMESTAMP NOT NULL,
    transaction_date DATE NOT NULL,
    transaction_hour SMALLINT NOT NULL,
    from_bank TEXT NOT NULL,
    from_account TEXT NOT NULL,
    to_bank TEXT NOT NULL,
    to_account TEXT NOT NULL,
    sender_entity_key TEXT NOT NULL,
    receiver_entity_key TEXT NOT NULL,
    amount_received NUMERIC NOT NULL,
    receiving_currency TEXT NOT NULL,
    amount_paid NUMERIC NOT NULL,
    payment_currency TEXT NOT NULL,
    payment_format TEXT NOT NULL,
    is_laundering SMALLINT NOT NULL,
    row_sha256 CHAR(64) NOT NULL,
    is_same_bank BOOLEAN NOT NULL,
    is_same_account BOOLEAN NOT NULL,
    is_cross_currency BOOLEAN NOT NULL,
    is_duplicate_candidate BOOLEAN NOT NULL,
    has_quality_issue BOOLEAN NOT NULL,
    quality_issue_codes TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    transformed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_staging_transaction
        FOREIGN KEY (transaction_id)
        REFERENCES raw.transactions(transaction_id),
    CONSTRAINT ck_staging_label
        CHECK (is_laundering IN (0, 1)),
    CONSTRAINT ck_staging_amounts
        CHECK (amount_received > 0 AND amount_paid > 0),
    CONSTRAINT ck_staging_hour
        CHECK (transaction_hour BETWEEN 0 AND 23),
    CONSTRAINT uq_staging_source_row
        UNIQUE (batch_id, source_row_number)
);

CREATE INDEX IF NOT EXISTS ix_staging_transaction_date
    ON staging.transactions(transaction_date);

CREATE INDEX IF NOT EXISTS ix_staging_sender
    ON staging.transactions(sender_entity_key);

CREATE INDEX IF NOT EXISTS ix_staging_receiver
    ON staging.transactions(receiver_entity_key);

CREATE INDEX IF NOT EXISTS ix_staging_duplicate
    ON staging.transactions(is_duplicate_candidate)
    WHERE is_duplicate_candidate = TRUE;

CREATE INDEX IF NOT EXISTS ix_staging_quality
    ON staging.transactions(has_quality_issue)
    WHERE has_quality_issue = TRUE;

CREATE TABLE IF NOT EXISTS staging.build_runs (
    build_id UUID PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status TEXT NOT NULL
        CHECK (status IN ('running', 'completed', 'failed')),
    source_rows BIGINT,
    staged_rows BIGINT,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS staging.quality_results (
    check_name TEXT PRIMARY KEY,
    observed_value BIGINT NOT NULL,
    expected_value BIGINT,
    status TEXT NOT NULL CHECK (status IN ('PASS', 'FAIL')),
    checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
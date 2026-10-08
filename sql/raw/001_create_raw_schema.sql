
CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.ingestion_batches (
    batch_id UUID PRIMARY KEY,
    source_filename TEXT NOT NULL,
    source_sha256 CHAR(64) NOT NULL,
    status TEXT NOT NULL
        CHECK (status IN ('running', 'completed', 'failed')),
    expected_rows BIGINT NOT NULL CHECK (expected_rows >= 0),
    loaded_rows BIGINT NOT NULL DEFAULT 0 CHECK (loaded_rows >= 0),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    CONSTRAINT uq_ingestion_source UNIQUE (source_sha256)
);

CREATE TABLE IF NOT EXISTS raw.transactions (
    transaction_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    batch_id UUID NOT NULL
        REFERENCES raw.ingestion_batches(batch_id),
    source_row_number BIGINT NOT NULL CHECK (source_row_number > 0),
    transaction_timestamp TIMESTAMP NOT NULL,
    from_bank TEXT NOT NULL,
    from_account TEXT NOT NULL,
    to_bank TEXT NOT NULL,
    to_account TEXT NOT NULL,
    amount_received NUMERIC NOT NULL,
    receiving_currency TEXT NOT NULL,
    amount_paid NUMERIC NOT NULL,
    payment_currency TEXT NOT NULL,
    payment_format TEXT NOT NULL,
    is_laundering SMALLINT NOT NULL
        CHECK (is_laundering IN (0, 1)),
    row_sha256 CHAR(64) NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_raw_source_row UNIQUE (batch_id, source_row_number)
);

CREATE INDEX IF NOT EXISTS ix_raw_transactions_timestamp
    ON raw.transactions(transaction_timestamp);

CREATE INDEX IF NOT EXISTS ix_raw_transactions_label
    ON raw.transactions(is_laundering);

CREATE INDEX IF NOT EXISTS ix_raw_transactions_from_account
    ON raw.transactions(from_bank, from_account);

CREATE INDEX IF NOT EXISTS ix_raw_transactions_to_account
    ON raw.transactions(to_bank, to_account);

CREATE INDEX IF NOT EXISTS ix_raw_transactions_batch
    ON raw.transactions(batch_id);

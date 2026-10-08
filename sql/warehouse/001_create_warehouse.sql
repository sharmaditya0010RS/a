CREATE SCHEMA IF NOT EXISTS warehouse;

CREATE TABLE IF NOT EXISTS warehouse.dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    calendar_year SMALLINT NOT NULL,
    calendar_month SMALLINT NOT NULL,
    calendar_day SMALLINT NOT NULL,
    calendar_quarter SMALLINT NOT NULL,
    day_of_week SMALLINT NOT NULL,
    is_weekend BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouse.dim_entity (
    entity_key TEXT PRIMARY KEY,
    bank_id TEXT NOT NULL,
    account_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouse.dim_currency (
    currency_key TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS warehouse.dim_payment_format (
    payment_format_key TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS warehouse.fact_transactions (
    transaction_id BIGINT PRIMARY KEY,
    date_key INTEGER NOT NULL REFERENCES warehouse.dim_date(date_key),
    sender_entity_key TEXT NOT NULL REFERENCES warehouse.dim_entity(entity_key),
    receiver_entity_key TEXT NOT NULL REFERENCES warehouse.dim_entity(entity_key),
    receiving_currency_key TEXT NOT NULL REFERENCES warehouse.dim_currency(currency_key),
    payment_currency_key TEXT NOT NULL REFERENCES warehouse.dim_currency(currency_key),
    payment_format_key TEXT NOT NULL REFERENCES warehouse.dim_payment_format(payment_format_key),
    transaction_timestamp TIMESTAMP NOT NULL,
    amount_received NUMERIC NOT NULL,
    amount_paid NUMERIC NOT NULL,
    is_laundering SMALLINT NOT NULL,
    is_same_bank BOOLEAN NOT NULL,
    is_same_account BOOLEAN NOT NULL,
    is_cross_currency BOOLEAN NOT NULL,
    is_duplicate_candidate BOOLEAN NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_fact_date
    ON warehouse.fact_transactions(date_key);

CREATE INDEX IF NOT EXISTS ix_fact_sender
    ON warehouse.fact_transactions(sender_entity_key);

CREATE INDEX IF NOT EXISTS ix_fact_receiver
    ON warehouse.fact_transactions(receiver_entity_key);

CREATE INDEX IF NOT EXISTS ix_fact_aml
    ON warehouse.fact_transactions(date_key)
    WHERE is_laundering = 1;

CREATE TABLE IF NOT EXISTS warehouse.mart_daily_aml (
    date_key INTEGER PRIMARY KEY REFERENCES warehouse.dim_date(date_key),
    transaction_count BIGINT NOT NULL,
    aml_positive_count BIGINT NOT NULL,
    total_amount_paid NUMERIC NOT NULL,
    cross_currency_count BIGINT NOT NULL,
    duplicate_candidate_count BIGINT NOT NULL,
    refreshed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

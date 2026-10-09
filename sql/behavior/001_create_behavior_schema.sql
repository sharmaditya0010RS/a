CREATE SCHEMA IF NOT EXISTS behavior;

CREATE TABLE IF NOT EXISTS behavior.entity_daily_activity (
    entity_key TEXT NOT NULL
        REFERENCES warehouse.dim_entity(entity_key),
    date_key INTEGER NOT NULL
        REFERENCES warehouse.dim_date(date_key),
    outgoing_count BIGINT NOT NULL DEFAULT 0,
    incoming_count BIGINT NOT NULL DEFAULT 0,
    outgoing_amount NUMERIC NOT NULL DEFAULT 0,
    incoming_amount NUMERIC NOT NULL DEFAULT 0,
    distinct_receivers BIGINT NOT NULL DEFAULT 0,
    distinct_senders BIGINT NOT NULL DEFAULT 0,
    cross_currency_outgoing BIGINT NOT NULL DEFAULT 0,
    high_value_outgoing BIGINT NOT NULL DEFAULT 0,
    refreshed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (entity_key, date_key)
);

CREATE INDEX IF NOT EXISTS ix_behavior_daily_date
    ON behavior.entity_daily_activity(date_key);

CREATE INDEX IF NOT EXISTS ix_behavior_daily_outgoing
    ON behavior.entity_daily_activity(outgoing_count DESC);

CREATE INDEX IF NOT EXISTS ix_behavior_daily_incoming
    ON behavior.entity_daily_activity(incoming_count DESC);

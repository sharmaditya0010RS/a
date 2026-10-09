CREATE TABLE IF NOT EXISTS behavior.entity_daily_signals (
    entity_key TEXT NOT NULL
        REFERENCES warehouse.dim_entity(entity_key),
    date_key INTEGER NOT NULL
        REFERENCES warehouse.dim_date(date_key),
    outgoing_count BIGINT NOT NULL,
    incoming_count BIGINT NOT NULL,
    distinct_receivers BIGINT NOT NULL,
    distinct_senders BIGINT NOT NULL,
    velocity_flag BOOLEAN NOT NULL,
    fan_in_flag BOOLEAN NOT NULL,
    fan_out_flag BOOLEAN NOT NULL,
    cross_currency_flag BOOLEAN NOT NULL,
    high_value_flag BOOLEAN NOT NULL,
    behavior_score SMALLINT NOT NULL
        CHECK (behavior_score BETWEEN 0 AND 100),
    behavior_level TEXT NOT NULL
        CHECK (behavior_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    scored_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (entity_key, date_key)
);

CREATE INDEX IF NOT EXISTS ix_behavior_signals_level
    ON behavior.entity_daily_signals(behavior_level);

CREATE INDEX IF NOT EXISTS ix_behavior_signals_date
    ON behavior.entity_daily_signals(date_key);

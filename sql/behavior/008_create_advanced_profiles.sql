
CREATE TABLE IF NOT EXISTS behavior.entity_daily_advanced (
    entity_key TEXT NOT NULL REFERENCES warehouse.dim_entity(entity_key),
    date_key INTEGER NOT NULL REFERENCES warehouse.dim_date(date_key),
    rapid_movement_count BIGINT NOT NULL DEFAULT 0,
    structuring_candidate_count BIGINT NOT NULL DEFAULT 0,
    structuring_amount NUMERIC NOT NULL DEFAULT 0,
    refreshed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (entity_key, date_key)
);

CREATE TABLE IF NOT EXISTS behavior.entity_risk_profiles (
    entity_key TEXT PRIMARY KEY REFERENCES warehouse.dim_entity(entity_key),
    active_days BIGINT NOT NULL,
    outgoing_transactions BIGINT NOT NULL,
    incoming_transactions BIGINT NOT NULL,
    velocity_days BIGINT NOT NULL,
    fan_in_days BIGINT NOT NULL,
    fan_out_days BIGINT NOT NULL,
    high_behavior_days BIGINT NOT NULL,
    rapid_movement_count BIGINT NOT NULL,
    structuring_candidate_days BIGINT NOT NULL,
    max_behavior_score SMALLINT NOT NULL,
    entity_risk_score SMALLINT NOT NULL
        CHECK (entity_risk_score BETWEEN 0 AND 100),
    entity_risk_level TEXT NOT NULL
        CHECK (entity_risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    refreshed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_entity_profiles_level
ON behavior.entity_risk_profiles(entity_risk_level);

CREATE INDEX IF NOT EXISTS ix_entity_advanced_date
ON behavior.entity_daily_advanced(date_key);

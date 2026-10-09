CREATE SCHEMA IF NOT EXISTS risk;

CREATE TABLE IF NOT EXISTS risk.rule_catalog (
    rule_code TEXT PRIMARY KEY,
    rule_name TEXT NOT NULL,
    description TEXT NOT NULL,
    risk_points SMALLINT NOT NULL CHECK (risk_points BETWEEN 1 AND 100),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS risk.transaction_scores (
    transaction_id BIGINT PRIMARY KEY
        REFERENCES warehouse.fact_transactions(transaction_id),
    risk_score SMALLINT NOT NULL CHECK (risk_score BETWEEN 0 AND 100),
    risk_level TEXT NOT NULL
        CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    triggered_rule_count SMALLINT NOT NULL,
    scored_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS risk.rule_hits (
    transaction_id BIGINT NOT NULL
        REFERENCES risk.transaction_scores(transaction_id),
    rule_code TEXT NOT NULL REFERENCES risk.rule_catalog(rule_code),
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (transaction_id, rule_code)
);

CREATE INDEX IF NOT EXISTS ix_risk_scores_level
    ON risk.transaction_scores(risk_level);

CREATE INDEX IF NOT EXISTS ix_risk_hits_rule
    ON risk.rule_hits(rule_code);

CREATE TABLE IF NOT EXISTS risk.alerts (
    alert_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    transaction_id BIGINT NOT NULL UNIQUE
        REFERENCES risk.transaction_scores(transaction_id),
    risk_score SMALLINT NOT NULL,
    risk_level TEXT NOT NULL,
    alert_status TEXT NOT NULL DEFAULT 'OPEN'
        CHECK (alert_status IN ('OPEN', 'IN_REVIEW', 'CLOSED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO risk.rule_catalog
    (rule_code, rule_name, description, risk_points)
VALUES
    ('HIGH_VALUE', 'High-value transfer',
     'Amount paid meets the configured high-value threshold', 35),
    ('CROSS_CURRENCY', 'Cross-currency transfer',
     'Payment and receiving currencies differ', 20),
    ('CROSS_BANK', 'Cross-bank transfer',
     'Sender and receiver banks differ', 15),
    ('DUPLICATE', 'Duplicate fingerprint candidate',
     'Transaction fingerprint appears more than once', 30)
ON CONFLICT (rule_code) DO NOTHING;

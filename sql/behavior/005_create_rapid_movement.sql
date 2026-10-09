CREATE TABLE IF NOT EXISTS behavior.rapid_movement (
    incoming_transaction_id BIGINT NOT NULL
        REFERENCES warehouse.fact_transactions(transaction_id),
    outgoing_transaction_id BIGINT NOT NULL
        REFERENCES warehouse.fact_transactions(transaction_id),
    entity_key TEXT NOT NULL
        REFERENCES warehouse.dim_entity(entity_key),
    incoming_timestamp TIMESTAMP NOT NULL,
    outgoing_timestamp TIMESTAMP NOT NULL,
    minutes_between NUMERIC NOT NULL,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (
        incoming_transaction_id,
        outgoing_transaction_id
    )
);

CREATE INDEX IF NOT EXISTS ix_rapid_movement_entity
    ON behavior.rapid_movement(entity_key);

CREATE INDEX IF NOT EXISTS ix_rapid_movement_outgoing
    ON behavior.rapid_movement(outgoing_transaction_id);

CREATE INDEX IF NOT EXISTS ix_fact_receiver_timestamp
ON warehouse.fact_transactions (
    receiver_entity_key,
    transaction_timestamp DESC,
    transaction_id DESC
);

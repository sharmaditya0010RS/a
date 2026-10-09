-- Phase 9: Investigation performance indexes
-- Execute outside an explicit transaction.
-- CONCURRENTLY reduces blocking of normal table writes.

CREATE INDEX CONCURRENTLY IF NOT EXISTS
    idx_fci_fact_sender_recent
ON warehouse.fact_transactions (
    sender_entity_key,
    transaction_timestamp DESC,
    transaction_id DESC
);

CREATE INDEX CONCURRENTLY IF NOT EXISTS
    idx_fci_fact_receiver_recent
ON warehouse.fact_transactions (
    receiver_entity_key,
    transaction_timestamp DESC,
    transaction_id DESC
);

CREATE INDEX CONCURRENTLY IF NOT EXISTS
    idx_fci_rule_hits_transaction
ON risk.rule_hits (
    transaction_id
);

CREATE INDEX CONCURRENTLY IF NOT EXISTS
    idx_fci_alerts_status_score
ON risk.alerts (
    alert_status,
    risk_score DESC,
    alert_id
);

ANALYZE warehouse.fact_transactions;
ANALYZE risk.rule_hits;
ANALYZE risk.alerts;
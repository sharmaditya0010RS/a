INSERT INTO behavior.rapid_movement (
    incoming_transaction_id,
    outgoing_transaction_id,
    entity_key,
    incoming_timestamp,
    outgoing_timestamp,
    minutes_between,
    detected_at
)
SELECT
    incoming.transaction_id,
    outgoing.transaction_id,
    outgoing.sender_entity_key,
    incoming.transaction_timestamp,
    outgoing.transaction_timestamp,
    EXTRACT(
        EPOCH FROM (
            outgoing.transaction_timestamp
            - incoming.transaction_timestamp
        )
    ) / 60,
    NOW()
FROM warehouse.fact_transactions outgoing
JOIN LATERAL (
    SELECT
        incoming_tx.transaction_id,
        incoming_tx.transaction_timestamp
    FROM warehouse.fact_transactions incoming_tx
    WHERE incoming_tx.receiver_entity_key =
          outgoing.sender_entity_key
      AND incoming_tx.transaction_timestamp <=
          outgoing.transaction_timestamp
      AND incoming_tx.transaction_timestamp >=
          outgoing.transaction_timestamp
          - INTERVAL '60 minutes'
      AND incoming_tx.transaction_id <>
          outgoing.transaction_id
    ORDER BY
        incoming_tx.transaction_timestamp DESC,
        incoming_tx.transaction_id DESC
    LIMIT 1
) incoming ON TRUE
WHERE outgoing.date_key = :date_key
ON CONFLICT (
    incoming_transaction_id,
    outgoing_transaction_id
) DO NOTHING;

CREATE TABLE IF NOT EXISTS risk.currency_thresholds (
    currency_key TEXT PRIMARY KEY,
    p99_amount NUMERIC NOT NULL,
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO risk.currency_thresholds
    (currency_key, p99_amount, calculated_at)
SELECT
    payment_currency_key,
    PERCENTILE_CONT(0.99) WITHIN GROUP
        (ORDER BY amount_paid::DOUBLE PRECISION)::NUMERIC,
    NOW()
FROM warehouse.fact_transactions
GROUP BY payment_currency_key
ON CONFLICT (currency_key) DO UPDATE SET
    p99_amount = EXCLUDED.p99_amount,
    calculated_at = NOW();

-- Daily and weekly summaries for the dashboard.

DROP TABLE IF EXISTS clean.daily_cashflow_summary;

CREATE TABLE clean.daily_cashflow_summary AS
SELECT region,
       transaction_date,
       SUM(CASE WHEN direction = 'inflow'  THEN amount ELSE 0 END) AS inflow,
       SUM(CASE WHEN direction = 'outflow' THEN amount ELSE 0 END) AS outflow,
       SUM(signed_amount)                                          AS net_cash_flow, --  inflows minus outflows
       COUNT(*)                                                    AS n_transactions
FROM clean.v_household_cashflow
WHERE quality_flag IS NULL OR quality_flag = 'large_shock'
GROUP BY region, transaction_date;


--  create the weekly view(for wuick weekly calculations)
CREATE INDEX IF NOT EXISTS idx_daily_summary_date ON clean.daily_cashflow_summary (transaction_date);

CREATE OR REPLACE VIEW clean.weekly_cashflow_summary AS
SELECT region,
       week_start,
       SUM(CASE WHEN direction = 'inflow'  THEN amount ELSE 0 END) AS inflow,
       SUM(CASE WHEN direction = 'outflow' THEN amount ELSE 0 END) AS outflow,
       SUM(signed_amount)                                          AS net_cash_flow,
       COUNT(*)                                                    AS n_transactions
FROM clean.v_household_cashflow
WHERE quality_flag IS NULL OR quality_flag = 'large_shock'
GROUP BY region, week_start;


-- The TEST;  the days with the biggest cash-flow drops by region
-- SELECT region, transaction_date, net_cash_flow
-- FROM clean.daily_cashflow_summary
-- ORDER BY net_cash_flow ASC
-- LIMIT 20;
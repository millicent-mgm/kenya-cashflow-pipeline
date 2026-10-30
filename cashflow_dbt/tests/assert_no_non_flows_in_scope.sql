-- cash-on-hand rows, fees and balances are not cash flows.
-- Rows returned = failures.
select transaction_id, class_code, direction, quality_flag
from {{ ref('fct_cashflow') }}
where in_scope and (class_code = 'cash' or direction is null)
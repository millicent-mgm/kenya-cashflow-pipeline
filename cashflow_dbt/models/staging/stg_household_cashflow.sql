select
    transaction_id,
    household_id,
    transaction_date,
    week_start,
    amount,
    direction,
    signed_amount,
    category_id,
    mode_id,
    is_large_shock,
    quality_flag
from {{ source('clean', 'household_cashflow_clean') }}
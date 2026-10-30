-- Rule 2 no amount above 2,000,000 KES. give warning only
{{ config(severity='warn') }}
select transaction_id, amount
from {{ ref('stg_household_cashflow') }}
where amount > 2000000
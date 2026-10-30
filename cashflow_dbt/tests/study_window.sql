-- Rule 1 every transaction date is inside the study window.
select transaction_id, transaction_date
from {{ ref('stg_household_cashflow') }}
where transaction_date < '2012-08-01' or transaction_date > '2013-12-31'
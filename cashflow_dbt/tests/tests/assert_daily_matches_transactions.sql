-- The daily table must add up to the same operating total as the transactions behind it.
with daily as (select sum(operating_net) as total from {{ ref('fct_daily_cashflow') }}),
     detail as (
         select sum(signed_amount) as total
         from {{ ref('fct_cashflow') }}
         where in_scope and flow_group in ('income_received', 'business_and_transfer_costs', 'household_spending')
     )
select daily.total as daily_total, detail.total as detail_total
from daily, detail
where abs(daily.total - detail.total) > 0.01
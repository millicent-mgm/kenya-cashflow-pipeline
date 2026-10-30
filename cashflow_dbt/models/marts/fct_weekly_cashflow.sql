select
    region,
    week_start,
    sum(case when flow_group = 'income_received'             then amount else 0 end) as income_received,
    sum(case when flow_group = 'business_and_transfer_costs' then amount else 0 end) as business_costs,
    sum(case when flow_group = 'household_spending'          then amount else 0 end) as household_spending,
    sum(case when flow_group in ('income_received', 'business_and_transfer_costs', 'household_spending')
             then signed_amount else 0 end)                                          as operating_net,
    sum(case when flow_group = 'financial' and direction = 'inflow'  then amount else 0 end) as financial_in,
    sum(case when flow_group = 'financial' and direction = 'outflow' then amount else 0 end) as financial_out,
    sum(case when flow_group = 'financial' then signed_amount else 0 end)            as financial_net,
    count(*)                                                                         as n_transactions
from {{ ref('fct_cashflow') }}
where in_scope
  and flow_group in ('income_received', 'business_and_transfer_costs', 'household_spending', 'financial')
group by region, week_start
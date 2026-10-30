select
    region,
    week_start,
    sum(case when direction = 'inflow'  then amount else 0 end) as inflow,
    sum(case when direction = 'outflow' then amount else 0 end) as outflow,
    sum(signed_amount)                                          as net_cash_flow,
    count(*)                                                    as n_transactions
from {{ ref('fct_cashflow') }}
where is_reportable
group by region, week_start
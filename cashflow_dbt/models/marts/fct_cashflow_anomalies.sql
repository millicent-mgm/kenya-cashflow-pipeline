-- One row per region per day, flagged when OPERATING net cash flow is unusually low
-- compared with that region's previous 28 days.
with daily as (
    select region, transaction_date, income_received, household_spending, operating_net, n_transactions
    from {{ ref('fct_daily_cashflow') }}
),

rolling as (
    select
        *,
        avg(operating_net)         over w as typical_net,
        stddev_samp(operating_net) over w as typical_spread,
        count(*)                   over w as days_of_history
    from daily
    window w as (
        partition by region
        order by transaction_date
        range between interval '28 days' preceding and interval '1 day' preceding
    )
)

select
    region, transaction_date, income_received, household_spending, operating_net, n_transactions,
    typical_net, typical_spread, days_of_history,
    coalesce(days_of_history >= 14 and operating_net < typical_net - 2 * typical_spread, false) as is_unusual_drop
from rolling
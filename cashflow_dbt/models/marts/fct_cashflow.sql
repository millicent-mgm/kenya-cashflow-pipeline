with base as (
    select
        f.transaction_id,
        f.household_id,
        f.transaction_date,
        f.week_start,
        f.amount,
        f.direction,
        f.signed_amount,
        f.class_code,
        c.original_category,
        c.standardised_category,
        coalesce(r.standardised_region, 'Unknown') as region,
        m.mode_of_payment,
        f.is_large_shock,
        f.quality_flag,
        f.diary_round,
        f.months_observed,
        f.is_research_gift,
        f.is_fee,
        f.is_in_kind,

        -- The row has no problem flag (a large shock is real money, so it stays)
        (f.quality_flag is null or f.quality_flag = 'large_shock') as is_reportable,

        
        
        (coalesce(f.diary_round, 99) >= 3
         and coalesce(f.months_observed, 99) >= 1
         and not f.is_research_gift) as is_study_sample,

        -- What kind of flow it is 
        case
            when f.class_code = 'income' and f.direction = 'inflow'  then 'income_received'
            when f.class_code = 'income' and f.direction = 'outflow' then 'business_and_transfer_costs'
            when f.class_code = 'opex'                               then 'household_spending'
            when f.class_code = 'findev'                             then 'financial'
            when f.class_code = 'assets'                             then 'assets'
            else 'not_a_cash_flow'
        end as flow_group
    from {{ ref('stg_household_cashflow') }} f
    left join {{ ref('stg_households') }}  h on h.household_id = f.household_id
    left join {{ ref('stg_regions') }}     r on r.region_id    = h.region_id
    left join {{ ref('stg_categories') }}  c on c.category_id  = f.category_id
    left join {{ ref('stg_modes') }}       m on m.mode_id      = f.mode_id
)

select
    *,
    -- The one rule every summary uses: a reliable, cash, in-sample row
    (is_reportable and is_study_sample and not is_in_kind) as in_scope
from base
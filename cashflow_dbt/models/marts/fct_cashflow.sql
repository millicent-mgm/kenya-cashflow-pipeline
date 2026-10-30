select
    f.transaction_id,
    f.household_id,
    f.transaction_date,
    f.week_start,
    f.amount,
    f.direction,
    f.signed_amount,
    c.original_category,
    c.standardised_category,
    coalesce(r.standardised_region, 'Unknown') as region,
    m.mode_of_payment,
    f.is_large_shock,
    f.quality_flag,
    (f.quality_flag is null or f.quality_flag = 'large_shock') as is_reportable  
from {{ ref('stg_household_cashflow') }} f
left join {{ ref('stg_households') }}  h on h.household_id = f.household_id
left join {{ ref('stg_regions') }}     r on r.region_id    = h.region_id
left join {{ ref('stg_categories') }}  c on c.category_id  = f.category_id
left join {{ ref('stg_modes') }}       m on m.mode_id      = f.mode_id
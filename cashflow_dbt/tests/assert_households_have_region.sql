-- Rule 3 every household has a known region. Warn if any, fail above 5% of the 298 households (14).
{{ config(severity='error', warn_if='>0', error_if='>14') }}
select h.household_id
from {{ ref('stg_households') }} h
left join {{ ref('stg_regions') }} r on r.region_id = h.region_id
where r.standardised_region is null or r.standardised_region = 'Unknown'
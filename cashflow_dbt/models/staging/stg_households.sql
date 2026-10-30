select household_id, region_id, first_trx_date, last_trx_date, days_of_obs
from {{ source('clean', 'dim_household') }}
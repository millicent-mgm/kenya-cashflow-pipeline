select region_id, original_region, standardised_region
from {{ source('clean', 'dim_region') }}
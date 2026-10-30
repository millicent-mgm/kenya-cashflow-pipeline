select category_id, original_category, standardised_category
from {{ source('clean', 'dim_category') }}
select mode_id, mode_of_payment
from {{ source('clean', 'dim_mode') }}

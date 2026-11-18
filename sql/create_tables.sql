-- Schema for the Kenya Financial Diaries cash-flow pipeline (PostgreSQL)

-- (this DELETES everything in the clean schema), 
-- DROP SCHEMA IF EXISTS clean CASCADE;

CREATE SCHEMA IF NOT EXISTS clean;

CREATE TABLE IF NOT EXISTS clean.dim_region (  -- creates the region table
    region_id           INT  PRIMARY KEY,
    original_region     TEXT,
    standardised_region TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS clean.dim_household (  -- creates the household table
    household_id   TEXT PRIMARY KEY,
    region_id      INT  REFERENCES clean.dim_region (region_id),
    first_trx_date DATE,
    last_trx_date  DATE,
    days_of_obs    INT
);

CREATE TABLE IF NOT EXISTS clean.dim_category (  --  creates the category table
    category_id           INT  PRIMARY KEY,
    original_category     TEXT,
    standardised_category TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS clean.dim_mode (  --  creates the mode table
    mode_id         INT  PRIMARY KEY,
    mode_of_payment TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS clean.household_cashflow_clean (  --creates the main/fact table
    transaction_id   BIGINT PRIMARY KEY,
    source_trx_id    BIGINT,
    household_id     TEXT   NOT NULL REFERENCES clean.dim_household (household_id), --  FOREIGN KEY
    transaction_date DATE,  --  the day the money moved (blank if the date was bad)
    week_start       DATE,
    amount           NUMERIC(14,2),  --  exact decimals (up to 14 digits, 2 after point)
    direction        TEXT CHECK (direction IN ('inflow', 'outflow')),
    signed_amount    NUMERIC(14,2),  --  exact decimals (up to 14 digits, 2 after point)
    category_id      INT REFERENCES clean.dim_category (category_id),  -- FOREIGN KEY
    mode_id          INT REFERENCES clean.dim_mode (mode_id),  --  FOREIGN KEY
    is_large_shock   BOOLEAN,  -- true or false
    quality_flag     TEXT CHECK (quality_flag IS NULL OR quality_flag IN (
                         'bad_date', 'balance_record', 'cash_on_hand_record', 'missing_amount',
                         'non_cash_fee', 'balance_sheet_movement', 'unknown_direction',
                         'zero_or_negative_amount', 'possible_duplicate', 'large_shock')),
    class_code       TEXT NOT NULL CHECK (class_code IN ('income', 'opex', 'findev', 'assets', 'cash')),
    diary_round      SMALLINT,                 -- which diary round the transaction belongs to
    months_observed  INT,                      -- months the household had been observed
    is_research_gift BOOLEAN,                  -- a gift from the research firm, not real income
    is_fee           BOOLEAN,                  -- a fee charged on an account
    is_in_kind       BOOLEAN,                  -- paid in goods or labour, not money
    CHECK (direction IS NULL     -- A direction must be inflow or outflow (or blank), a flag must be one of the ten labels, the class one of the five README classes, and an inflow can't have a negative signed amount.
           OR (direction = 'inflow'  AND signed_amount >= 0)
           OR (direction = 'outflow' AND signed_amount <= 0))
);

--  created indexes so that  postgres goes straight to locate the columns and not read all >400,000 rows
CREATE INDEX IF NOT EXISTS idx_cashflow_date      ON clean.household_cashflow_clean (transaction_date);
CREATE INDEX IF NOT EXISTS idx_cashflow_household ON clean.household_cashflow_clean (household_id);
CREATE INDEX IF NOT EXISTS idx_cashflow_category  ON clean.household_cashflow_clean (category_id);



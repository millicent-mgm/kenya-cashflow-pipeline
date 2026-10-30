from pathlib import Path 
import pandas as pd

from clean_transform import load_raw, clean_dates, standardise, build_columns #loading the cleaned data
from extract import setup_logging, extract

setup_logging()
df = extract()
df = load_raw()
df = clean_dates(df)
df = standardise(df)
out = build_columns(df)

print(out.shape)

#filling in the blanks with "unknown"
text_cols = ["original_category", "standardised_category",
             "original_region", "standardised_region", "mode_of_payment"]

for col in text_cols:
    out[col] = out[col].astype("object").where(out[col].notna(), "Unknown")

#bulding the 3 lookup tables
def add_dim(frame, cols, id_col):
    dim = frame[cols].drop_duplicates().reset_index(drop=True)   # showss list of distinct values
    dim.insert(0, id_col, dim.index + 1)                         # number them 1, 2, 3...
    frame = frame.merge(dim, on=cols, how="left")                # put that number on every transaction
    return dim, frame    

dim_category, out = add_dim(out, ["original_category", "standardised_category"], "category_id")
dim_region,   out = add_dim(out, ["original_region", "standardised_region"], "region_id")
dim_mode,     out = add_dim(out, ["mode_of_payment"], "mode_id")

print(len(out), len(dim_category), len(dim_region), len(dim_mode))

#building the household table(giving one row per household with its first 
# and last diary dates and the days observed. Then attach each household’s region number)

hh_region = out[["household_id", "region_id"]].drop_duplicates("household_id")

dim_household = (
    df.groupby("hh_ids")
      .agg(first_trx_date=("first_trx_date_hh_clean", "min"),
           last_trx_date=("last_trx_date_hh_clean", "max"),
           days_of_obs=("tot_hh_daysofobs", "max"))
      .reset_index()
      .rename(columns={"hh_ids": "household_id"})
      .merge(hh_region, on="household_id", how="left")
)
dim_household = dim_household[["household_id", "region_id", "first_trx_date",
                               "last_trx_date", "days_of_obs"]]

print(len(dim_household))

#create the main table
household_cashflow_clean = out[[
    "transaction_id", "source_trx_id", "household_id", "transaction_date", "week_start",
    "amount", "direction", "signed_amount", "category_id", "mode_id",
    "is_large_shock", "quality_flag",
]]

print(household_cashflow_clean.shape)

fact = household_cashflow_clean
print("unique ids:", fact["transaction_id"].is_unique)
print("households not in dim:", (~fact["household_id"].isin(dim_household["household_id"])).sum())
print("missing category / mode ids:", fact["category_id"].isna().sum(), fact["mode_id"].isna().sum())
print("households with no region:", dim_household["region_id"].isna().sum())

out_dir = Path("data/processed")
out_dir.mkdir(parents=True, exist_ok=True)

household_cashflow_clean.to_csv(out_dir / "household_cashflow_clean.csv", index=False)
dim_household.to_csv(out_dir / "dim_household.csv", index=False)
dim_region.to_csv(out_dir / "dim_region.csv", index=False)
dim_category.to_csv(out_dir / "dim_category.csv", index=False)
dim_mode.to_csv(out_dir / "dim_mode.csv", index=False)
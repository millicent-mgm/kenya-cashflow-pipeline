from pathlib import Path
import numpy as np
import pandas as pd

RAW_FILE = Path("data/raw/diaries_transactions_all.csv")

CATEGORY_COL = "trx_family_desc"   # or "trx_prx_purpose"
direction_map = {"inflow": "inflow",
                  "outflow": "outflow"}   
category_fixes = {}                # e.g. {"mpesa": "m-pesa"} to merge spelling variants (keys lowercase)

# Household IDs start with a 4-letter site code (KELDL02 -> KELD). Region comes from this code.
# KZIM (3 households) is left out on purpose until its region is confirmed it shows as unmapped.
SITE_TO_REGION = {
    "KVIH": "Vihiga",
    "KMAK": "Makueni",
    "KELD": "Eldoret",
    "KMOM": "Mombasa",
    "KNBO": "Nairobi",
}

# Rows that record an account balance (a stock), not money moving in or out
BALANCE_MODES = {"closing balance", "starting balance"}

DATE_COLS = [
    "trx_date",
    "first_trx_date_hh", "last_trx_date_hh",
    "first_trx_date_acc", "last_trx_date_acc",
    "int_date", "first_int_date",
]

# words that mean "no value"
MISSING_MARKERS = {"", "n/a", "na", "none", "null", "nan", "-"}

# IDs: only strip stray spaces
ID_COLS = ["hh_ids", "account_ids", "m_ids_trx", "m_ids_owner"]

# text columns that get a tidy copy ending in _std (the original stays untouched)
TEXT_COLS = ["trx_direction", "trx_family_desc", "trx_prx_purpose",
             "trx_mode_desc", "trx_outlet"]


def clean_text(s):
    s = s.astype("string").str.strip().str.lower().str.replace(r"\s+", " ", regex=True)
    return s.mask(s.isin(MISSING_MARKERS))      # placeholder words become properly missing


def load_raw():
    return pd.read_csv(RAW_FILE, low_memory=False)   


def clean_dates(df):
    for col in DATE_COLS:
        text = df[col].str.strip().replace("", pd.NA)
        parsed = pd.to_datetime(text, format="%d%b%Y", errors="coerce")
        failed = parsed.isna() & text.notna()
        print(f"{col}: {failed.sum()} failed | blank: {text.isna().sum()} | "
              f"range: {parsed.min().date()} to {parsed.max().date()}")
        df[col + "_clean"] = parsed
    return df


def standardise(df):
    # IDs: remove stray spaces only
    for col in ID_COLS:
        df[col] = df[col].astype("string").str.strip()

    # site code = first 4 characters of the household ID (used for region)
    df["site_code"] = df["hh_ids"].str[:4].str.upper()

    # text columns: tidy version goes into a NEW column ending in _std
    for col in TEXT_COLS:
        df[col + "_std"] = clean_text(df[col])

    print("\n--- standardising ---")
    for col in TEXT_COLS:
        print(f"{col}: {df[col].nunique()} distinct as written -> {df[col + '_std'].nunique()} after")
    return df


def build_columns(df):
    out = pd.DataFrame(index=df.index)

    # The file's trx_id is NOT unique (its long numbers were rounded), so make our own key
    out["transaction_id"]   = np.arange(1, len(df) + 1)
    out["source_trx_id"]    = df["trx_id"]          # kept for reference only
    out["household_id"]     = df["hh_ids"]
    out["transaction_date"] = df["trx_date_clean"]
    out["week_start"]       = df["trx_date_clean"].dt.to_period("W").dt.start_time
    out["amount"]           = df["trx_value_kes"]

    # what kind of transaction it is, and what the study excludes
    out["class_code"]       = df["trx_class_code"]                   # income, opex, findev, assets, cash
    out["diary_round"]      = df["trx_dq_round"].astype("Int64")     # whole number, so it loads into SMALLINT
    out["months_observed"]  = df["trx_stdtime_mnths_hh"]
    out["is_research_gift"] = df["ddd_gift"].eq(1)
    out["is_fee"]           = df["trx_fee"].eq(1)
    out["is_in_kind"]       = df["trx_mode_desc_std"].str.startswith("in-kind", na=False).astype(bool)

    # direction (uses the tidy column)
    out["direction"] = df["trx_direction_std"].astype("object").map(direction_map)

    # signed amount: + for inflow, - for outflow
    amt = out["amount"].abs()
    out["signed_amount"] = np.select(
        [out["direction"] == "inflow", out["direction"] == "outflow"],
        [amt, -amt],
        default=np.nan,
    )

    # category, region, mode
    out["original_category"]     = df[CATEGORY_COL]
    out["standardised_category"] = df[CATEGORY_COL + "_std"].replace(category_fixes).str.title()
    out["original_region"]       = df["site_code"]
    out["standardised_region"]   = df["site_code"].map(SITE_TO_REGION)
    out["mode_of_payment"]       = df["trx_mode_desc_std"].str.title()

    # large shock: above the 99th percent for its direction
    cutoff = out.groupby("direction")["amount"].transform(lambda s: s.quantile(0.99))
    out["is_large_shock"] = out["amount"] > cutoff

    # quality flag: first problem found wins, blank if the row is fine
    is_balance = df["trx_mode_desc_std"].isin(BALANCE_MODES) | df["account_startclose_balance"].notna()
    conditions = [
        out["transaction_date"].isna(),
        is_balance,                                                      # starting or closing balance (a stock)
        df["trx_class_code"].eq("cash"),                                 # cash on hand or lost: not a cash flow
        out["amount"].isna(),
        out["direction"].isna() & out["is_fee"],                         # automatic fee: not a cash flow
        out["direction"].isna() & df["trx_bsheet_direction"].notna(),    # moves a balance, not household cash
        out["direction"].isna(),
        out["amount"] <= 0,
        df.duplicated(keep="first"),
        out["is_large_shock"],
    ]
    labels = ["bad_date", "balance_record", "cash_on_hand_record", "missing_amount",
              "non_cash_fee", "balance_sheet_movement", "unknown_direction",
              "zero_or_negative_amount", "possible_duplicate", "large_shock"]
    conditions = [pd.Series(c, index=out.index).fillna(False).astype(bool).to_numpy()
                  for c in conditions]
    out["quality_flag"] = pd.Series(np.select(conditions, labels, default=""),
                                    index=out.index).replace("", pd.NA)
    return out


def main():
    df = load_raw()
    df = clean_dates(df)
    df = standardise(df)          

    print("\n--- direction values (tidied) ---")
    print(df["trx_direction_std"].value_counts(dropna=False))
    print("Negative amounts:", (df["trx_value_kes"] < 0).sum())
    print("Distinct categories:", df["trx_family_desc"].nunique(), "(family_desc) |",
          df["trx_prx_purpose"].nunique(), "(purpose)")

    out = build_columns(df)

    print("\n--- checks on the new columns ---")
    print("Rows in vs out:", len(df), len(out))
    print("transaction_id unique:", out["transaction_id"].is_unique)
    print("Rows with no signed_amount:", out["signed_amount"].isna().sum())
    print("Year match:", (df["trx_date_clean"].dt.year == df["trx_year"]).mean())
    print("Month match:", (df["trx_date_clean"].dt.month == df["trx_month"]).mean())
    print(out["quality_flag"].value_counts(dropna=False))
    print("\n--- classes (the README lists income 114,417, opex 283,942, findev 77,070) ---")
    print(out["class_code"].value_counts(dropna=False))

    print("\n--- region check (households per region) ---")
    households = out.drop_duplicates("household_id")
    print(households["standardised_region"].value_counts(dropna=False))
    print("Unmapped households:", households.loc[households["standardised_region"].isna(),
                                                 "household_id"].tolist())

    print("\n--- rows still flagged unknown_direction (after balance records) ---")
    rest = (out["quality_flag"].astype("string") == "unknown_direction").fillna(False).astype(bool)
    print("Count:", rest.sum())
    print(df.loc[rest, "trx_mode_desc_std"].value_counts(dropna=False).head(8))
    print(df.loc[rest, "trx_bsheet_direction"].value_counts(dropna=False))
    print(df.loc[rest, "trx_family_desc"].value_counts(dropna=False).head(8))

    print(out.head())


if __name__ == "__main__":
    main()
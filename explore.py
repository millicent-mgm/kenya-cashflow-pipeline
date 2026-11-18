import pandas as pd  

df = pd.read_csv("data/raw/diaries_transactions_all.csv", low_memory=False)

print (df.shape)   #rows and columns
print (df.columns.tolist())  # columns name
print (df.dtypes)  #data types
print (df.head(10))  #firstrows

pd.set_option("display.max_rows", None)  #shows every row without the middle dots
nulls = df.isna().sum().to_frame("nulls")  #adds up True columns (empty) and turns into a small table with one column called nulls
print(nulls.sort_values("nulls", ascending=False))   #puts the emptiest columns first

print("Exact duplicate rows:", df.duplicated().sum())

print(df["trx_prx_purpose"].value_counts().head(50)) #check text columns for messy spellings
print(df["trx_family_desc"].value_counts().head(50))
print(df["trx_mode_desc"].value_counts().head(50))
print(df["trx_outlet"].value_counts().head(50))

print(df["trx_value_kes"].describe()) #check for money column, max,min,outliers

print(df["trx_date"].head()) #checks the date column
print(df["trx_date"].dtype)
print(df["trx_date"].isna().sum())
print(df["trx_date"].str.len().value_counts()) #checkk length of the dtype i.e text if same length then follow one format
df["trx_date_clean"]=pd.to_datetime(df["trx_date"], format="%d%b%Y", errors="coerce") #Convert to a real date,bad value becomes blank instead of crashing
failed = df["trx_date_clean"].isna() & df["trx_date"].notna()
print("Failed to convert:", failed.sum())
print(df.loc[failed, "trx_date"].value_counts().head(20))   # shows what the bad values look like

print(df.dtypes)

date_cols = [
    "first_trx_date_hh", "last_trx_date_hh",
    "first_trx_date_acc", "last_trx_date_acc",
    "int_date", "first_int_date",
]

for col in date_cols:
    # tidy the text first: remove stray spaces and treat empty strings as missing
    text = df[col].str.strip().replace("", pd.NA)

    # convert to a real date; anything that doesn't match becomes NaT (blank date)
    parsed = pd.to_datetime(text, format="%d%b%Y", errors="coerce")

    # a failure = the file had a value, but it couldn't be read as a date
    failed = parsed.isna() & text.notna()

    print(f"{col}: {failed.sum()} failed | blank: {text.isna().sum()} | "
          f"range: {parsed.min().date()} to {parsed.max().date()}")
    if failed.sum() > 0:
        print(text[failed].value_counts().head(10))

    # keep the original text column untouched; put the real dates in a new column
    df[col + "_clean"] = parsed

pattern = "mombasa|nairobi|makueni|vihiga|eldoret|el doret"

for col in df.columns:  #searched for the region names,to see if one already told me the region
    if pd.api.types.is_string_dtype(df[col]):
        hits = df[col].str.contains(pattern, case=False, na=False).sum()
        if hits > 0:
            print(col, hits)


# 1. trx_id problem
print("Extra copies of a trx_id:", df["trx_id"].duplicated().sum())
print("Extra exact-duplicate rows:", df.duplicated().sum())
print("IDs ending in 000:", (df["trx_id"] % 1000 == 0).mean())  #id were rounded so transactions could share the same ID;cannot be trusted

# 2. rows with no direction: what are they?
unk = df["trx_direction"].fillna("").astype(str).str.strip().eq("")
print(df.loc[unk, "trx_mode_desc"].value_counts(dropna=False).head(8))
print(df.loc[unk, "trx_class_desc"].value_counts(dropna=False).head(8))

# 3. household ID prefixes
ids = df.drop_duplicates("hh_ids")["hh_ids"]
print("Households:", len(ids))
print(ids.str[:4].value_counts())            

#now pulled out one household to see the data made sense
x = df[(df["hh_ids"] == "KMOMT32") & (df["trx_date_clean"] == "2013-03-04")]
print(x[["hh_ids", "trx_date", "trx_value_kes", "trx_direction", "trx_family_desc", "trx_mode_desc"]])







print("\n--- classes ---")
print(df["trx_class_code"].value_counts(dropna=False))
print(df.groupby(["trx_class_code", "trx_direction"], dropna=False)["trx_value_kes"].agg(["count", "sum"]))

print("\n--- rows the study excludes when it calculates income ---")
inc = df[df["trx_class_code"] == "income"]
print("income rows:", len(inc))
print("  in diary rounds 1-2:", (inc["trx_dq_round"] < 3).sum())
print("  in a household's first month:", (inc["trx_stdtime_mnths_hh"] < 1).sum())
print("  research-firm gifts:", (inc["ddd_gift"] == 1).sum())

print("\n--- rows with no direction ---")
nd = df[df["trx_direction"].isna()]
print(nd.groupby(["trx_mode_desc", "trx_fee"], dropna=False).size().sort_values(ascending=False).head(10))
print(df["account_startclose_balance"].value_counts(dropna=False))

print("\n--- zero-value rows and in-kind ---")
zero = df[df["trx_value_kes"] == 0]
print("zero-value rows:", len(zero), "| with an in-kind value:", (zero["trx_inkind_value_kes"] > 0).sum())
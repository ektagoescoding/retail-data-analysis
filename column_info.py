import pandas as pd
import polars as pl


def clean_dataframe(df):
    df = df.copy()

    # Remove completely empty rows
    df = df.dropna(how="all").reset_index(drop=True)

    # Remove completely empty columns
    df = df.loc[:, df.notna().any(axis=0)]

    # Remove duplicate rows
    df = df.drop_duplicates().reset_index(drop=True)

    # Convert numeric-like strings
    for col in df.columns:
        if df[col].dtype == "object":
            try:
                converted = pd.to_numeric(df[col], errors="coerce")
                if converted.notna().mean() >= 0.7:
                    df[col] = converted
            except Exception:
                pass

    # Fill missing values
    for col in df.columns:
        s = df[col]

        if s.isna().all():
            df = df.drop(columns=[col])
            continue

        if pd.api.types.is_numeric_dtype(s):
            df[col] = s.fillna(s.median())
        elif pd.api.types.is_datetime64_any_dtype(s):
            df[col] = s.fillna(s.dropna().median())
        else:
            mode_value = s.mode(dropna=True)
            fill_value = mode_value.iloc[0] if not mode_value.empty else "Unknown"
            df[col] = s.fillna(fill_value)

    return df


def get_column_info(df):
    df = clean_dataframe(df)

    rows = []
    for col in df.columns:
        s = df[col]

        rows.append({
            "Column": col,
            "Data Type": str(s.dtype),
            "Non-Null Count": int(s.notna().sum()),
            "Null Count": int(s.isna().sum()),
            "Missing Values": int(s.isna().sum()),
            "Duplicate Values": int(s.duplicated().sum()),
            "Unique Values": int(s.nunique()),
        })

    return pd.DataFrame(rows)


def get_column_info_pl(df: pl.DataFrame):
    rows = df.height

    rows_data = []
    for col in df.columns:
        s = df[col]
        null_count = s.null_count()
        unique_count = s.n_unique()
        missing_pct = round((null_count / rows) * 100, 2) if rows > 0 else 0.0

        rows_data.append({
            "Column": col,
            "dtype": str(s.dtype),
            "Null Count": null_count,
            "Unique Count": unique_count,
            "Missing %": missing_pct
        })

    return pl.DataFrame(rows_data)
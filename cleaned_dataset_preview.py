import pandas as pd
import polars as pl


def _to_pandas(df):
    if isinstance(df, pl.DataFrame):
        return df.to_pandas()
    return df.copy()


def remove_empty_rows_and_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.dropna(how="all").reset_index(drop=True)
    df = df.loc[:, df.notna().any(axis=0)]
    return df


def normalize_numeric_like_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == object:
            converted = pd.to_numeric(df[col], errors="coerce")
            if converted.notna().mean() >= 0.7:
                df[col] = converted
    return df


def clean_dataset_pandas(df) -> pd.DataFrame:
    df = _to_pandas(df)
    df = remove_empty_rows_and_columns(df)
    df = normalize_numeric_like_columns(df)
    df = df.drop_duplicates().reset_index(drop=True)

    for col in df.columns:
        series = df[col]
        if series.isna().all():
            df = df.drop(columns=[col])
            continue

        if pd.api.types.is_numeric_dtype(series):
            df[col] = series.fillna(series.median())
        elif pd.api.types.is_datetime64_any_dtype(series):
            df[col] = series.fillna(series.dropna().median())
        else:
            mode = series.mode(dropna=True)
            fill = mode.iloc[0] if not mode.empty else "Unknown"
            df[col] = series.fillna(fill)

    return df


def get_cleaned_preview(df, limit: int = 200) -> pd.DataFrame:
    cleaned = clean_dataset_pandas(df)
    return cleaned.head(limit)
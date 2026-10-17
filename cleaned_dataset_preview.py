import re
import pandas as pd
import polars as pl
from word2number import w2n

MISSING_TOKENS = {"", "nan", "null", "n/a", "na"}


def _make_unique_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    columns = []
    seen = {}

    for col in df.columns:
        name = str(col).strip()
        if name == "":
            name = "column"

        if name in seen:
            seen[name] += 1
            columns.append(f"{name}_{seen[name]}")
        else:
            seen[name] = 0
            columns.append(name)

    df.columns = columns
    return df


def _to_pandas(df):
    if isinstance(df, pl.DataFrame):
        return df.to_pandas()
    return df.copy()


def is_real_missing(value):
    if value is None:
        return True

    if isinstance(value, str):
        text = value.strip()
        return text == "" or text.lower() in MISSING_TOKENS

    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def normalize_missing_strings(value):
    if is_real_missing(value):
        return pd.NA
    return value


def parse_age_value(value):
    if is_real_missing(value):
        return pd.NA

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)

    if isinstance(value, str):
        text = (
            value.strip().lower()
            .replace("_", " ")
            .replace(",", " ")
            .replace("-", " ")
        )

        if text in MISSING_TOKENS or text == "none":
            return pd.NA

        text = re.sub(r"[^a-z0-9\s.]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        if not text:
            return pd.NA

        if re.fullmatch(r"\d+(\.\d+)?", text):
            return float(text)

        try:
            return float(w2n.word_to_num(text))
        except (ValueError, TypeError, IndexError):
            pass

        match = re.search(r"(\d+(?:\.\d+)?)", text)
        if match:
            return float(match.group(1))

    return pd.NA


def fill_missing_for_column(df, col):
    s = df[col].map(normalize_missing_strings)
    col_name = str(col).strip().lower()

    if s.isna().all():
        if "email" in col_name:
            df[col] = "unknown@email.com"
        elif "phone" in col_name or "mobile" in col_name:
            df[col] = "Not Provided"
        else:
            df[col] = "Unknown"
        return

    numeric_col_names = {
        "age", "ages", "customer_age", "customer age",
        "quantity", "qty", "total", "price", "sales", "count"
    }

    if col_name in numeric_col_names:
        converted = pd.to_numeric(s.map(parse_age_value), errors="coerce")
        if converted.notna().any():
            converted = converted.fillna(converted.median())
        df[col] = converted
        return

    if "email" in col_name:
        df[col] = s.fillna("unknown@email.com")
        return

    if "phone" in col_name or "mobile" in col_name:
        df[col] = s.fillna("Not Provided")
        return

    if any(key in col_name for key in
           ["name", "address", "city", "country", "state", "region"]):
        df[col] = s.fillna("Unknown")
        return

    if pd.api.types.is_numeric_dtype(s):
        numeric = pd.to_numeric(s, errors="coerce")
        if numeric.notna().any():
            df[col] = numeric.fillna(numeric.median())
            return

    if pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s):
        numeric = pd.to_numeric(s, errors="coerce")
        if numeric.notna().sum() > 0:
            df[col] = numeric.fillna(numeric.median())
        else:
            df[col] = s.fillna("Unknown")
        return

    df[col] = s.fillna("Unknown")


def clean_dataset_pandas(df):
    df = _to_pandas(df)
    df = _make_unique_columns(df)

    for col in df.columns:
        df[col] = df[col].map(normalize_missing_strings)

    for col in df.columns:
        fill_missing_for_column(df, col)

    df = df.dropna(how="all")
    df = df.dropna(axis=1, how="all")

    # Final safeguard before plotting
    if df.columns.duplicated().any():
        df = _make_unique_columns(df)

    return df

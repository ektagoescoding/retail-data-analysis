import pandas as pd
import polars as pl
from typing import Union


def _to_pandas(df: Union[pd.DataFrame, pl.DataFrame]) -> pd.DataFrame:
    if isinstance(df, pl.DataFrame):
        return df.to_pandas()
    return df.copy()


def numerical_descriptive_stats(df: Union[pd.DataFrame, pl.DataFrame], round_n: int = 4) -> pd.DataFrame:
    """
    Return descriptive statistics for numerical columns only.
    Columns returned: count, mean, std, min, 25%, 50%, max
    """
    pdf = _to_pandas(df)
    num = pdf.select_dtypes(include="number")
    if num.shape[1] == 0:
        return pd.DataFrame(columns=["count", "mean", "std", "min", "25%", "50%", "max"])

    desc = num.describe(percentiles=[0.25, 0.5]).transpose()
    # ensure required columns exist
    for c in ("count", "mean", "std", "min", "25%", "50%", "max"):
        if c not in desc.columns:
            desc[c] = pd.NA

    result = desc[["count", "mean", "std", "min", "25%", "50%", "max"]].copy()
    # make count integer if possible
    try:
        result["count"] = result["count"].astype("Int64")
    except Exception:
        pass

    # round floats
    float_cols = result.select_dtypes(include="number").columns.difference(["count"])
    result[float_cols] = result[float_cols].round(round_n)

    return result.reset_index().rename(columns={"index": "column"})
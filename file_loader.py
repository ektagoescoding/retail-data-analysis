import polars as pl
from pathlib import Path


def load_file(file):
    extension = Path(file.name).suffix.lower()

    # --------------------------------------------------
    # CSV
    # --------------------------------------------------
    if extension == ".csv":

        # Read everything as text first.
        # This preserves values such as:
        # 0
        # 0.00
        # 100.50
        #
        # No zero value will be converted to missing.
        df = pl.read_csv(
            file,
            infer_schema=False,
            try_parse_dates=False,
            ignore_errors=False
        )

        return df

    # --------------------------------------------------
    # EXCEL
    # --------------------------------------------------
    if extension in [".xlsx", ".xls"]:

        df = pl.read_excel(file)

        return df

    # --------------------------------------------------
    # JSON
    # --------------------------------------------------
    if extension == ".json":

        try:
            return pl.read_ndjson(file)

        except Exception:

            file.seek(0)

            return pl.read_json(file)

    # --------------------------------------------------
    # INVALID FILE
    # --------------------------------------------------
    raise ValueError(
        "Unsupported file format. Use CSV, Excel, or JSON."
    )
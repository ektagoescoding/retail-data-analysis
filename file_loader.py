import polars as pl
from pathlib import Path
import io


def load_file(file):
    extension = Path(file.name).suffix.lower()

    if extension == ".csv":
        # read robustly, avoid aggressive type inference, then cast to Utf8
        # pass the file-like object (Streamlit UploadedFile)
        df = pl.read_csv(
            file,
            try_parse_dates=False,
            ignore_errors=True,
            infer_schema_length=5000
        )
        df = df.with_columns([pl.col(c).cast(pl.Utf8) for c in df.columns])
        return df

    if extension in [".xlsx", ".xls"]:
        # polars supports reading excel; pass file-like object
        df = pl.read_excel(file)
        # ensure string columns to avoid mixed-type issues
        df = df.with_columns([pl.col(c).cast(pl.Utf8) for c in df.columns])
        return df

    if extension == ".json":
        # try ndjson first, fallback to regular json
        try:
            return pl.read_ndjson(file)
        except Exception:
            return pl.read_json(file)

    raise ValueError("Unsupported file format. Use CSV, Excel, or JSON.")
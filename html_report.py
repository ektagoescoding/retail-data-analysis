
import html
from datetime import datetime

import pandas as pd
import streamlit as st


def _as_pandas(df):
    if isinstance(df, pd.DataFrame):
        return df.copy()

    try:
        return df.to_pandas()
    except Exception:
        pass

    return pd.DataFrame(df)


def _is_missing(value):
    if value is None:
        return True

    # Nested JSON objects and arrays are not automatically missing.
    if isinstance(value, (dict, list, tuple, set)):
        return False

    try:
        result = pd.isna(value)
        if isinstance(result, bool) and result:
            return True
        # Handle NumPy boolean results.
        if not hasattr(result, "__len__") and bool(result):
            return True
    except (TypeError, ValueError):
        pass

    if isinstance(value, str):
        return value.strip().lower() in {
            "", "nan", "none", "null", "n/a", "na", "<na>"
        }

    return False


def _safe(value):
    if _is_missing(value):
        return "N/A"

    return html.escape(str(value))


def _missing_count(missing):
    """Count missing values safely from a count, mapping, or DataFrame."""

    if missing is None:
        return 0

    if isinstance(missing, (int, float)):
        return int(missing)

    if isinstance(missing, pd.DataFrame):
        return sum(
            _is_missing(value)
            for column in missing.columns
            for value in missing[column]
        )

    if isinstance(missing, pd.Series):
        return sum(_is_missing(value) for value in missing.tolist())

    if isinstance(missing, dict):
        total = 0

        for value in missing.values():
            if isinstance(value, dict):
                # Nested column information: count its missing values.
                total += _missing_count(value)
            elif isinstance(value, (list, tuple, set)):
                # Lists may contain individual missing values.
                total += sum(_is_missing(item) for item in value)
            elif isinstance(value, (int, float)):
                # A numeric value here represents a precomputed count.
                total += int(value)
            else:
                # Do not try int() on strings or arbitrary objects.
                continue

        return total

    try:
        return int(missing)
    except (TypeError, ValueError, OverflowError):
        return 0


def generate_html_report(raw_df, cleaned_full, file_name, missing):
    raw_df = _as_pandas(raw_df)
    cleaned_full = _as_pandas(cleaned_full)

    generated_time = datetime.now().strftime("%d %B %Y, %I:%M %p")

    total_rows = len(raw_df)
    total_columns = len(raw_df.columns)
    duplicate_rows = int(raw_df.duplicated().sum())

    # Count missing values directly from the original dataset.
    total_missing = sum(
        _is_missing(value)
        for column in raw_df.columns
        for value in raw_df[column]
    )

    numeric_columns = cleaned_full.select_dtypes(
        include=["number"]
    ).columns.tolist()

    categorical_columns = [
        column for column in cleaned_full.columns
        if column not in numeric_columns
    ]

    overview_rows = f"""
        <tr><td>Total Rows</td><td>{total_rows:,}</td></tr>
        <tr><td>Total Columns</td><td>{total_columns:,}</td></tr>
        <tr><td>Missing Values</td><td>{total_missing:,}</td></tr>
        <tr><td>Duplicate Rows</td><td>{duplicate_rows:,}</td></tr>
        <tr><td>Numeric Columns</td><td>{len(numeric_columns):,}</td></tr>
        <tr><td>Categorical Columns</td><td>{len(categorical_columns):,}</td></tr>
    """

    column_rows = []

    for column in cleaned_full.columns:
        series = cleaned_full[column]

        missing_in_column = sum(
            _is_missing(value) for value in series
        )
        unique_count = series.nunique(dropna=True)

        column_rows.append(
            f"<tr>"
            f"<td>{_safe(column)}</td>"
            f"<td>{_safe(series.dtype)}</td>"
            f"<td>{missing_in_column:,}</td>"
            f"<td>{unique_count:,}</td>"
            f"</tr>"
        )

    column_table_rows = "\n".join(column_rows)

    insights = []

    if total_missing:
        insights.append(
            f"The dataset contains {total_missing:,} missing values."
        )
    else:
        insights.append("No missing values were detected.")

    if duplicate_rows:
        insights.append(
            f"The dataset contains {duplicate_rows:,} duplicate rows."
        )
    else:
        insights.append("No duplicate rows were detected.")

    insights.append(
        f"There are {len(numeric_columns)} numeric columns and "
        f"{len(categorical_columns)} categorical or other columns."
    )

    suggestions = []

    if total_missing:
        suggestions.append(
            "Review missing values and choose appropriate replacements "
            "or removal rules before analysis."
        )

    if duplicate_rows:
        suggestions.append(
            "Review duplicate records and remove them if they are "
            "unintended."
        )

    if not suggestions:
        suggestions.append(
            "Continue monitoring data quality and validate values "
            "before making business decisions."
        )

    insights_html = "".join(
        f"<li>{_safe(item)}</li>" for item in insights
    )
    suggestions_html = "".join(
        f"<li>{_safe(item)}</li>" for item in suggestions
    )

    report_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Data Analysis Report</title>
      <style>
        body {{
          font-family: Arial, sans-serif;
          margin: 30px;
          color: #222;
          line-height: 1.5;
        }}
        h1, h2 {{ color: #222; }}
        table {{
          border-collapse: collapse;
          width: 100%;
          margin-bottom: 24px;
        }}
        th, td {{
          border: 1px solid #ddd;
          padding: 9px;
          text-align: left;
          overflow-wrap: anywhere;
        }}
        th {{ background: #f2f2f2; }}
        tr:nth-child(even) {{ background: #fafafa; }}
      </style>
    </head>
    <body>
      <h1><strong>Data Analysis Report</strong></h1>

      <p>
        <strong>Dataset:</strong> {_safe(file_name)}<br>
        <strong>Generated:</strong> {_safe(generated_time)}
      </p>

      <h2>Dataset Overview</h2>
      <table>
        <thead><tr><th>Metric</th><th>Value</th></tr></thead>
        <tbody>{overview_rows}</tbody>
      </table>

      <h2>Column Summary</h2>
      <table>
        <thead>
          <tr>
            <th>Column</th>
            <th>Data Type</th>
            <th>Missing</th>
            <th>Unique</th>
          </tr>
        </thead>
        <tbody>{column_table_rows}</tbody>
      </table>

      <h2>Top Insights</h2>
      <ul>{insights_html}</ul>

      <h2>Suggestions</h2>
      <ul>{suggestions_html}</ul>

      <h2>Conclusions</h2>
      <p>
        The report summarizes the uploaded dataset's structure and basic
        data-quality indicators. Review the findings and validate the
        data before using it for business decisions.
      </p>
    </body>
    </html>
    """

    return report_html


def download_html_report(raw_df, cleaned_df, dataset_name, missing=None):
    raw_df = _as_pandas(raw_df)
    cleaned_df = _as_pandas(cleaned_df)

    report_html = generate_html_report(
        raw_df,
        cleaned_df,
        dataset_name,
        missing
    )

    st.download_button(
        label="Download HTML Report",
        data=report_html,
        file_name=f"{dataset_name.rsplit('.', 1)[0]}_report.html",
        mime="text/html",
        key="download_html_report",
    )
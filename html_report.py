import streamlit as st
import pandas as pd


# =========================================================
# GENERATE HTML REPORT
# =========================================================

def generate_html_report(raw_df, cleaned_df, dataset_name):

    generated_time = pd.Timestamp.now().strftime(
        "%d %b %Y, %I:%M %p"
    )

    # =====================================================
    # RAW DATASET INFORMATION
    # =====================================================

    total_rows = len(raw_df)

    total_columns = len(raw_df.columns)

    missing_values = int(
        raw_df.isna().sum().sum()
    )

    duplicate_rows = int(
        raw_df.duplicated().sum()
    )

    numeric_columns = len(
        raw_df.select_dtypes(include="number").columns
    )

    categorical_columns = len(
        raw_df.select_dtypes(exclude="number").columns
    )

    # =====================================================
    # DATASET OVERVIEW
    # =====================================================

    overview_html = f"""
    <table>
        <tr>
            <th>Information</th>
            <th>Value</th>
        </tr>

        <tr>
            <td>Total Rows</td>
            <td>{total_rows:,}</td>
        </tr>

        <tr>
            <td>Total Columns</td>
            <td>{total_columns:,}</td>
        </tr>

        <tr>
            <td>Missing Values</td>
            <td>{missing_values:,}</td>
        </tr>

        <tr>
            <td>Duplicate Rows</td>
            <td>{duplicate_rows:,}</td>
        </tr>

        <tr>
            <td>Numeric Columns</td>
            <td>{numeric_columns:,}</td>
        </tr>

        <tr>
            <td>Categorical Columns</td>
            <td>{categorical_columns:,}</td>
        </tr>
    </table>
    """

    # =====================================================
    # RAW DATASET COLUMN SUMMARY
    # =====================================================

    column_summary = pd.DataFrame({
        "Column": raw_df.columns,
        "Data Type": raw_df.dtypes.astype(str).values,
        "Missing": raw_df.isna().sum().values,
        "Unique": [
            raw_df[column].nunique(dropna=True)
            for column in raw_df.columns
        ]
    })

    column_summary_html = column_summary.to_html(
        index=False,
        border=0
    )

    # =====================================================
    # CLEANED DATASET ANALYSIS
    # =====================================================

    cleaned_numeric = cleaned_df.select_dtypes(
        include="number"
    )

    cleaned_categorical = cleaned_df.select_dtypes(
        exclude="number"
    )

    # =====================================================
    # TOP INSIGHTS
    # =====================================================

    insights = []

    # Cleaned dataset rows
    insights.append(
        f"The cleaned dataset contains "
        f"<b>{len(cleaned_df):,}</b> rows."
    )

    # Missing values after cleaning
    cleaned_missing = int(
        cleaned_df.isna().sum().sum()
    )

    if cleaned_missing > 0:

        insights.append(
            f"The cleaned dataset contains "
            f"<b>{cleaned_missing:,}</b> missing values."
        )

    else:

        insights.append(
            "No missing values remain in the cleaned dataset."
        )

    # Duplicate rows after cleaning
    cleaned_duplicates = int(
        cleaned_df.duplicated().sum()
    )

    if cleaned_duplicates > 0:

        insights.append(
            f"The cleaned dataset contains "
            f"<b>{cleaned_duplicates:,}</b> duplicate rows."
        )

    else:

        insights.append(
            "No duplicate rows remain in the cleaned dataset."
        )

    # Numerical insights
    for column in cleaned_numeric.columns[:3]:

        mean_value = cleaned_numeric[column].mean()

        if pd.notna(mean_value):

            insights.append(
                f"The average value of "
                f"<b>{column}</b> is "
                f"<b>{mean_value:,.2f}</b>."
            )

    # Categorical insights
    for column in cleaned_categorical.columns[:2]:

        mode = cleaned_df[column].mode()

        if not mode.empty:

            insights.append(
                f"The most frequent value in "
                f"<b>{column}</b> is "
                f"<b>{mode.iloc[0]}</b>."
            )

    insights_html = ""

    for insight in insights:

        insights_html += f"""
        <li>{insight}</li>
        """

    # =====================================================
    # SUGGESTIONS
    # =====================================================

    suggestions = []

    if missing_values > 0:

        suggestions.append(
            "Review the missing values identified "
            "in the original dataset."
        )

    if duplicate_rows > 0:

        suggestions.append(
            "Review the duplicate records identified "
            "in the original dataset."
        )

    if len(cleaned_numeric.columns) > 0:

        suggestions.append(
            "Use descriptive statistics to analyze "
            "the numerical columns."
        )

    if len(cleaned_categorical.columns) > 0:

        suggestions.append(
            "Analyze categorical columns using "
            "frequency distributions."
        )

    if not suggestions:

        suggestions.append(
            "The dataset appears ready for further analysis."
        )

    suggestions_html = ""

    for suggestion in suggestions:

        suggestions_html += f"""
        <li>{suggestion}</li>
        """

    # =====================================================
    # CONCLUSION
    # =====================================================

    conclusion = (
        f"The original dataset contains "
        f"<b>{total_rows:,}</b> rows and "
        f"<b>{total_columns:,}</b> columns. "
    )

    if missing_values > 0:

        conclusion += (
            f"It contains "
            f"<b>{missing_values:,}</b> missing values. "
        )

    else:

        conclusion += (
            "It contains no missing values. "
        )

    if duplicate_rows > 0:

        conclusion += (
            f"There are also "
            f"<b>{duplicate_rows:,}</b> duplicate rows. "
        )

    else:

        conclusion += (
            "No duplicate rows were detected. "
        )

    conclusion += (
        f"After cleaning, the dataset contains "
        f"<b>{len(cleaned_df):,}</b> rows."
    )

    # =====================================================
    # COMPLETE HTML REPORT
    # =====================================================

    html_report = f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<title>DATA ANALYSIS REPORT</title>

<style>

body {{
    font-family: Arial, sans-serif;
    background-color: #f5f5f5;
    margin: 40px;
    color: #222;
}}

.container {{
    max-width: 1000px;
    margin: auto;
    background-color: white;
    padding: 35px;
    border-radius: 10px;
}}

h1 {{
    text-align: center;
    font-size: 30px;
    margin-bottom: 10px;
}}

h2 {{
    margin-top: 35px;
    border-bottom: 2px solid #ddd;
    padding-bottom: 8px;
}}

.metadata {{
    text-align: center;
    color: #666;
    margin-bottom: 30px;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 15px;
}}

th,
td {{
    border: 1px solid #ddd;
    padding: 10px;
    text-align: left;
}}

th {{
    background-color: #eeeeee;
    font-weight: bold;
}}

tr:nth-child(even) {{
    background-color: #fafafa;
}}

li {{
    margin: 10px 0;
    line-height: 1.5;
}}

.conclusion {{
    background-color: #f2f2f2;
    padding: 18px;
    line-height: 1.7;
    border-radius: 6px;
}}

</style>

</head>


<body>

<div class="container">


<h1>
    DATA ANALYSIS REPORT
</h1>


<div class="metadata">

    Dataset: <b>{dataset_name}</b>

    &nbsp; | &nbsp;

    Generated: <b>{generated_time}</b>

</div>


<!-- =====================================================
     DATASET OVERVIEW
===================================================== -->

<h2>
    Dataset Overview
</h2>

{overview_html}


<!-- =====================================================
     COLUMN SUMMARY
===================================================== -->

<h2>
    Column Summary
</h2>

{column_summary_html}


<!-- =====================================================
     TOP INSIGHTS
===================================================== -->

<h2>
    Top Insights
</h2>

<ul>

{insights_html}

</ul>


<!-- =====================================================
     SUGGESTIONS
===================================================== -->

<h2>
    Suggestions
</h2>

<ul>

{suggestions_html}

</ul>


<!-- =====================================================
     CONCLUSIONS
===================================================== -->

<h2>
    Conclusions
</h2>

<div class="conclusion">

{conclusion}

</div>


</div>

</body>

</html>
"""

    return html_report


# =========================================================
# DOWNLOAD HTML REPORT
# =========================================================

def download_html_report(raw_df, cleaned_df, dataset_name):

    html_report = generate_html_report(
        raw_df,
        cleaned_df,
        dataset_name
    )

    st.download_button(
        label="Generate & Download HTML Report",
        data=html_report,
        file_name="data_analysis_report.html",
        mime="text/html"
    )
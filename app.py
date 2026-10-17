import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Retail Analyzer",
    page_icon="📊",
    layout="wide"
)

from file_loader import load_file
from cleaned_dataset_preview import clean_dataset_pandas
from data_visualization import show_visualizations
from html_report import download_html_report
from dashboard import show_dashboard


def dataset_label(file_name):
    return (
        file_name.rsplit(".", 1)[0]
        .replace("_", " ")
        .replace("-", " ")
        .title()
    )


def _as_pandas(df):
    if isinstance(df, pd.DataFrame):
        return df.copy()

    try:
        return df.to_pandas()
    except Exception:
        pass

    return pd.DataFrame(df)


def is_missing_value(value):
    if value is None:
        return True

    if isinstance(value, (dict, list, tuple, set)):
        return False

    try:
        result = pd.isna(value)
        if not hasattr(result, "__len__") and bool(result):
            return True
    except (TypeError, ValueError):
        pass

    if isinstance(value, str):
        return value.strip().lower() in {
            "", "nan", "none", "null", "n/a", "na", "<na>"
        }

    return False


def count_missing_values(df):
    df = _as_pandas(df)
    return sum(
        is_missing_value(value)
        for column in df.columns
        for value in df[column]
    )


def highlight_missing_cells(df):
    def highlight(value):
        if is_missing_value(value):
            return "background-color: #FCE4E4; color: #9B1C1C;"
        return ""

    return df.style.map(highlight)


def show_dataset_analysis_tab(raw_df, cleaned_df, missing_count, file_name):
    st.write("## Dataset Information")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Rows", f"{len(raw_df):,}")
    col2.metric("Columns", f"{len(raw_df.columns):,}")
    col3.metric("Missing Values", f"{missing_count:,}")

    file_size = getattr(st.session_state.get("uploaded_file"), "size", None)
    file_size_text = f"{file_size / 1024:.2f} KB" if file_size is not None else "N/A"
    col4.metric("File Size", file_size_text)

    st.write("## Dataset Preview")
    st.dataframe(highlight_missing_cells(raw_df), use_container_width=True, height=500)

    st.write("## Column Information")
    column_info = pd.DataFrame({
        "Column Name": raw_df.columns,
        "Data Type": [str(raw_df[col].dtype) for col in raw_df.columns],
        "Missing Values": [int(raw_df[col].isna().sum()) for col in raw_df.columns],
        "Unique Values": [int(raw_df[col].nunique(dropna=True)) for col in raw_df.columns],
    })
    st.dataframe(column_info, use_container_width=True)

    st.write("## Cleaned Dataset Preview")
    st.dataframe(cleaned_df, use_container_width=True, height=500)

    st.write("## Descriptive Statistics")
    numeric_df = cleaned_df.select_dtypes(include=["number"])
    if not numeric_df.empty:
        st.dataframe(numeric_df.describe().T, use_container_width=True)
    else:
        st.info("No numeric columns available.")

    st.write("## Data Visualizations")
    show_visualizations(cleaned_df)

    st.write("## Generate Report")
    download_html_report(raw_df, cleaned_df, file_name, missing_count)


def show_dashboard_tab(cleaned_df, file_name):
    clean_name = file_name.rsplit(".", 1)[0]
    clean_name = clean_name.replace(" (1)", "").replace(" (2)", "").replace(" (3)", "")
    show_dashboard(cleaned_df, clean_name)


st.title("📊 Retail Analyzer")
st.caption("Intelligent Retail Data Analysis & Decision Support System")

uploaded_file = st.file_uploader(
    "Upload your dataset",
    type=["csv", "xlsx", "xls", "json"],
    key="uploaded_file"
)

if uploaded_file is None:
    st.info("Please upload a file to begin analysis.")
    st.stop()

try:
    loaded_df = load_file(uploaded_file)
    raw_df = _as_pandas(loaded_df)
    cleaned_df = _as_pandas(clean_dataset_pandas(raw_df))
    missing_count = count_missing_values(raw_df)

    st.session_state["raw_df"] = raw_df
    st.session_state["cleaned_df"] = cleaned_df
    st.session_state["dataset_name"] = uploaded_file.name
    st.session_state["missing"] = missing_count

    tab1, tab2 = st.tabs(["Dataset Analysis", "Dashboard"])

    with tab1:
        show_dataset_analysis_tab(raw_df, cleaned_df, missing_count, uploaded_file.name)

    with tab2:
        show_dashboard_tab(cleaned_df, uploaded_file.name)

except Exception as e:
    st.error(f"Error while processing dataset: {e}")
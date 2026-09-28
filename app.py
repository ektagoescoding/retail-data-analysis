import streamlit as st
import polars as pl
import pandas as pd
from file_loader import load_file
from cleaned_dataset_preview import get_cleaned_preview, clean_dataset_pandas
from descriptive_stats import numerical_descriptive_stats 
from data_visualization import show_visualizations


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="📊 Retail Analyzer",
    page_icon="📊",
    layout="wide"
)


# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------

st.markdown(
    """
    <style>

    /* Main title */
    h1 {
        font-size: 32px !important;
        font-weight: 700 !important;
    }

    /* Section headings */
    h2 {
        font-size: 24px !important;
        font-weight: 700 !important;
    }

    /* Sub-section headings */
    h3 {
        font-size: 24px !important;
        font-weight: 700 !important;
        margin-top: 1rem;
    }

    /* Make ONLY metric headings bold */
    div[data-testid="stMetric"] label {
        font-size: 16px !important;
        font-weight: 700 !important;
    }

    div[data-testid="stMetric"] label p {
        font-size: 16px !important;
        font-weight: 700 !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# TITLE
# --------------------------------------------------

st.title("📊 Retail Analyzer")

st.write(
    "Intelligent Retail Data Analysis & Decision Support System"
)


# --------------------------------------------------
# FILE SIZE FORMATTER
# --------------------------------------------------

def sizeof_fmt(n):

    if n is None:
        return "N/A"

    n = float(n)

    for unit in ("B", "KB", "MB", "GB", "TB"):

        if n < 1024.0:
            return f"{n:.2f} {unit}"

        n /= 1024.0

    return f"{n:.2f} PB"


# --------------------------------------------------
# FILE UPLOADER
# --------------------------------------------------

uploaded_file = st.file_uploader(
    "Upload your dataset",
    type=["csv", "xlsx", "xls", "json"]
)


# --------------------------------------------------
# PROCESS UPLOADED FILE
# --------------------------------------------------

if uploaded_file:

    try:

        # Load file
        try:
            df = load_file(uploaded_file)
        except Exception:
            # silent fallbacks: try pandas (all columns as strings), then relaxed polars
            try:
                uploaded_file.seek(0)
                name = getattr(uploaded_file, "name", "") or ""
                if name.lower().endswith((".csv", ".txt")):
                    pd_df = pd.read_csv(uploaded_file, dtype=str, low_memory=False)
                elif name.lower().endswith((".xls", ".xlsx")):
                    uploaded_file.seek(0)
                    pd_df = pd.read_excel(uploaded_file, dtype=str)
                elif name.lower().endswith(".json"):
                    uploaded_file.seek(0)
                    pd_df = pd.read_json(uploaded_file)
                else:
                    uploaded_file.seek(0)
                    pd_df = pd.read_csv(uploaded_file, dtype=str, low_memory=False)

                df = pl.DataFrame(pd_df)
            except Exception:
                try:
                    uploaded_file.seek(0)
                    df = pl.read_csv(
                        uploaded_file,
                        infer_schema_length=10000,
                        ignore_errors=True
                    )
                except Exception as final_exc:
                    st.error("Failed to load file.")
                    raise final_exc


        # Ensure Polars DataFrame
        if not isinstance(df, pl.DataFrame):
            df = pl.DataFrame(df)

        st.success("File loaded successfully!")


        # --------------------------------------------------
        # DATASET INFORMATION
        # --------------------------------------------------

        st.write("## Dataset Information")

        file_name = getattr(
            uploaded_file,
            "name",
            "unknown"
        )


        # --------------------------------------------------
        # GET FILE SIZE
        # --------------------------------------------------

        file_size_bytes = None

        try:

            file_size_bytes = getattr(
                uploaded_file,
                "size",
                None
            )

        except Exception:

            file_size_bytes = None


        if file_size_bytes is None:

            try:

                buf = getattr(
                    uploaded_file,
                    "getbuffer",
                    None
                )

                if callable(buf):

                    file_size_bytes = (
                        uploaded_file
                        .getbuffer()
                        .nbytes
                    )

                else:

                    file_size_bytes = getattr(
                        uploaded_file,
                        "_file",
                        None
                    )

                    if file_size_bytes is not None:

                        file_size_bytes = (
                            file_size_bytes
                            .getbuffer()
                            .nbytes
                        )

            except Exception:

                file_size_bytes = None


        # --------------------------------------------------
        # MEMORY USAGE
        # --------------------------------------------------

        memory_usage_bytes = None

        try:

            memory_usage_bytes = (
                df.estimated_size()
            )

        except Exception:

            try:

                if df.height * df.width <= 200_000:

                    memory_usage_bytes = (
                        df
                        .to_pandas()
                        .memory_usage(deep=True)
                        .sum()
                    )

            except Exception:

                memory_usage_bytes = None


        # --------------------------------------------------
        # FILE INFORMATION
        # --------------------------------------------------

        col_a, col_b, col_c = st.columns(3)

        col_a.markdown(
            f"**File name:** {file_name}"
        )

        col_b.markdown(
            f"**File size:** "
            f"{sizeof_fmt(file_size_bytes)}"
        )

        col_c.markdown(
            f"**Memory usage (estimated):** "
            f"{sizeof_fmt(memory_usage_bytes)}"
        )


        # --------------------------------------------------
        # DATASET OVERVIEW
        # --------------------------------------------------

        st.write("## Dataset Overview")

        rows = df.height
        cols = df.width


        # --------------------------------------------------
        # NULL VALUES
        # --------------------------------------------------

        null_counts_raw = df.null_count()

        try:

            col_nulls = null_counts_raw.to_list()

        except Exception:

            col_nulls = [
                int(
                    df
                    .select(
                        pl.col(c)
                        .is_null()
                        .sum()
                    )
                    .to_series()[0]
                )
                for c in df.columns
            ]


        missing = sum(
            int(n)
            for n in col_nulls
        )


        # --------------------------------------------------
        # DUPLICATES
        # --------------------------------------------------

        duplicates = (
            rows -
            df.unique().height
        )


        # --------------------------------------------------
        # KPI CARDS
        # --------------------------------------------------

        k1, k2, k3, k4 = st.columns(4)

        k1.markdown(
            f'''
            <div>
                <strong style="font-size:16px;">Total rows</strong><br>
                <span style="font-size:22px; font-weight:400;">{rows:,}</span>
            </div>
            ''',
            unsafe_allow_html=True
        )

        k2.markdown(
            f'''
            <div>
                <strong style="font-size:16px;">Total columns</strong><br>
                <span style="font-size:22px; font-weight:400;">{cols:,}</span>
            </div>
            ''',
            unsafe_allow_html=True
        )

        k3.markdown(
            f'''
            <div>
                <strong style="font-size:16px;">Missing values</strong><br>
                <span style="font-size:22px; font-weight:400;">{missing:,}</span>
            </div>
            ''',
            unsafe_allow_html=True
        )

        k4.markdown(
            f'''
            <div>
                <strong style="font-size:16px;">Duplicate rows</strong><br>
                <span style="font-size:22px; font-weight:400;">{duplicates:,}</span>
            </div>
            ''',
            unsafe_allow_html=True
        )
        # --------------------------------------------------
        # COMPLETE DATASET
        # --------------------------------------------------

        st.write("### Complete Dataset")

        try:
            raw_df = df.to_pandas()

            # allow styling for very large dataframe
            pd.set_option("styler.render.max_elements", max(1, raw_df.shape[0] * raw_df.shape[1]))

            def highlight_missing_cells(df):
                def style_cell(value):
                    # missing values
                    if pd.isna(value):
                        return "background-color: #f8d7da; color: #842029; font-weight: 600;"

                    # blank strings / spaces only
                    if isinstance(value, str):
                        if value.strip() == "":
                            return "background-color: #f8d7da; color: #842029; font-weight: 600;"

                    return ""

                return df.style.map(style_cell)

            st.dataframe(highlight_missing_cells(raw_df), use_container_width=True, height=800)

        except Exception:
            st.table(df.to_dicts())

        # --------------------------------------------------
        # CLEANED DATASET PREVIEW + COLUMN INFO
        # --------------------------------------------------
        try:
            # create full cleaned dataset (use this for stats) and a preview for display
            cleaned_full = clean_dataset_pandas(raw_df)
            cleaned_preview = cleaned_full.head(200)

            st.write("### Column information (cleaned preview)")
            cols_info = pd.DataFrame({
                "column": cleaned_preview.columns,
                "dtype": cleaned_preview.dtypes.astype(str).values
            })
            st.dataframe(cols_info, use_container_width=True)

            st.write("### Cleaned Dataset Preview")
            st.dataframe(cleaned_preview, use_container_width=True, height=400)

            # --------------------------------------------------
            # DESCRIPTIVE STATISTICS
            # --------------------------------------------------

            st.write("### Descriptive Statistics")

            # Use the cleaned dataset for statistics
            numeric_data = cleaned_full.select_dtypes(include="number")

            if not numeric_data.empty:
                st.write("#### Numerical Descriptive Statistics")

                descriptive_stats = numeric_data.describe().T

                # Add useful statistics
                descriptive_stats["median"] = numeric_data.median()
                descriptive_stats["missing"] = numeric_data.isna().sum()
                descriptive_stats["missing_%"] = (
                    numeric_data.isna().mean() * 100
                ).round(2)

                # Arrange columns in a readable order
                descriptive_stats = descriptive_stats[
                    [
                        "count",
                        "mean",
                        "median",
                        "std",
                        "min",
                        "25%",
                        "50%",
                        "75%",
                        "max",
                        "missing",
                        "missing_%"
                    ]
                ]

                st.dataframe(
                    descriptive_stats.round(2),
                    use_container_width=True
                )
            # Categorical column statistics
            categorical_data = cleaned_full.select_dtypes(
                exclude="number"
            )

            if not categorical_data.empty:
                #st.write("#### Descriptive Statistics")

                categorical_stats = pd.DataFrame({
                    "column": categorical_data.columns,
                    "count": [
                        categorical_data[col].count()
                        for col in categorical_data.columns
                    ],
                    "unique": [
                        categorical_data[col].nunique(dropna=True)
                        for col in categorical_data.columns
                    ],
                    "missing": [
                        categorical_data[col].isna().sum()
                        for col in categorical_data.columns
                    ],
                    "most_frequent": [
                        categorical_data[col].mode().iloc[0]
                        if not categorical_data[col].mode().empty
                        else "N/A"
                        for col in categorical_data.columns
                    ]
                })

                categorical_stats["missing_%"] = (
                    categorical_stats["missing"] / len(cleaned_full) * 100
                ).round(2)

                st.dataframe(
                    categorical_stats,
                    use_container_width=True
                )

            # --------------------------------------------------
            # DATA VISUALIZATION
            # --------------------------------------------------

            show_visualizations(cleaned_full)

        except Exception:
            # silently skip if cleaning fails
            pass


    # --------------------------------------------------
    # ERROR HANDLING
    # --------------------------------------------------

    except Exception as error:

        st.error(
            str(error)
        )
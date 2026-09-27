import streamlit as st
import polars as pl

from file_loader import load_file


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
        df = load_file(uploaded_file)

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

            pdf = df.to_pandas()

            st.dataframe(
                pdf,
                height=800
            )

        except Exception:

            st.table(
                df.to_dicts()
            )


    # --------------------------------------------------
    # ERROR HANDLING
    # --------------------------------------------------

    except Exception as error:

        st.error(
            str(error)
        )
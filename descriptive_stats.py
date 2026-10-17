import streamlit as st


def show_descriptive_statistics(df):
    st.subheader("📊 Descriptive Statistics")

    # Numeric columns
    numeric_df = df.select_dtypes(include="number")

    if not numeric_df.empty:
        st.write("### Numeric Columns")
        st.dataframe(numeric_df.describe())

    else:
        st.info("No numeric columns found.")

    # Categorical columns
    categorical_df = df.select_dtypes(exclude="number")

    if not categorical_df.empty:
        st.write("### Categorical Columns")

        stats = categorical_df.describe().T
        st.dataframe(stats)

    # Missing values
    st.write("### Missing Values")

    missing = df.isnull().sum()
    missing_percentage = (missing / len(df)) * 100

    missing_stats = {
        "Missing Values": missing,
        "Missing %": missing_percentage.round(2)
    }

    st.dataframe(missing_stats)
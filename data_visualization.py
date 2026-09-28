import streamlit as st
import pandas as pd
import plotly.express as px


def show_visualizations(df):

    st.write("## Data Visualization")

    data = df.copy()

    # Convert every column to numeric where possible
    numeric_columns = []

    for col in data.columns:

        converted = pd.to_numeric(
            data[col],
            errors="coerce"
        )

        # If at least one value can be converted,
        # treat the column as numeric
        if converted.notna().sum() > 0:
            data[col] = converted
            numeric_columns.append(col)

    # Columns that are not numeric
    categorical_columns = [
        col for col in data.columns
        if col not in numeric_columns
    ]

    # ==================================================
    # LINE CHART
    # ==================================================

    st.write("### Line Chart")

    if len(numeric_columns) >= 1:

        x_column = st.selectbox(
            "Select X-axis",
            data.columns,
            key="line_x"
        )

        y_column = st.selectbox(
            "Select Y-axis",
            numeric_columns,
            key="line_y"
        )

        chart_data = data[
            [x_column, y_column]
        ].dropna()

        if len(chart_data) > 0:

            fig = px.line(
                chart_data,
                x=x_column,
                y=y_column,
                markers=True,
                title=f"{y_column} over {x_column}"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


    # ==================================================
    # BAR CHART
    # ==================================================

    st.write("### Bar Chart")

    if len(categorical_columns) >= 1 and len(numeric_columns) >= 1:

        category = st.selectbox(
            "Select Category",
            categorical_columns,
            key="bar_category"
        )

        value = st.selectbox(
            "Select Value",
            numeric_columns,
            key="bar_value"
        )

        bar_data = (
            data.groupby(category)[value]
            .sum()
            .reset_index()
            .sort_values(
                value,
                ascending=False
            )
            .head(15)
        )

        fig = px.bar(
            bar_data,
            x=category,
            y=value,
            title=f"{value} by {category}"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


    # ==================================================
    # PIE CHART
    # ==================================================

    st.write("### Pie Chart")

    if len(categorical_columns) >= 1 and len(numeric_columns) >= 1:

        pie_category = st.selectbox(
            "Select Category",
            categorical_columns,
            key="pie_category"
        )

        pie_value = st.selectbox(
            "Select Value",
            numeric_columns,
            key="pie_value"
        )

        pie_data = (
            data.groupby(pie_category)[pie_value]
            .sum()
            .reset_index()
            .sort_values(
                pie_value,
                ascending=False
            )
            .head(10)
        )

        fig = px.pie(
            pie_data,
            names=pie_category,
            values=pie_value,
            title=f"{pie_value} Distribution"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


    # ==================================================
    # SCATTER PLOT
    # ==================================================

    st.write("### Scatter Plot")

    if len(numeric_columns) >= 2:

        x_column = st.selectbox(
            "Select X-axis",
            numeric_columns,
            key="scatter_x"
        )

        y_column = st.selectbox(
            "Select Y-axis",
            numeric_columns,
            key="scatter_y"
        )

        scatter_data = data[
            [x_column, y_column]
        ].dropna()

        fig = px.scatter(
            scatter_data,
            x=x_column,
            y=y_column,
            title=f"{y_column} vs {x_column}"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


    # ==================================================
    # DATA TYPE INFORMATION
    # ==================================================

    with st.expander("Visualization Data Information"):

        st.write("Numeric columns:")
        st.write(numeric_columns)

        st.write("Categorical columns:")
        st.write(categorical_columns)
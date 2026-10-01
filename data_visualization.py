import streamlit as st
import pandas as pd
import plotly.express as px


def show_visualizations(df):

    st.write("## Data Visualization")

    # --------------------------------------------------
    # CONVERT DATA TO PANDAS
    # --------------------------------------------------

    if not isinstance(df, pd.DataFrame):
        try:
            data = df.to_pandas()
        except Exception:
            data = pd.DataFrame(df)
    else:
        data = df.copy()

    # --------------------------------------------------
    # DETECT DATE COLUMNS
    # --------------------------------------------------

    date_columns = []

    for col in data.columns:

        # Do not try to convert numeric columns to dates
        if pd.api.types.is_numeric_dtype(data[col]):
            continue

        converted_date = pd.to_datetime(
            data[col],
            errors="coerce",
            format="mixed"
        )

        if len(data) > 0:

            valid_ratio = (
                converted_date.notna().sum()
                / len(data)
            )

            # At least 80% of values must be valid dates
            if valid_ratio >= 0.80:
                date_columns.append(col)

    # --------------------------------------------------
    # DETECT NUMERIC COLUMNS
    # --------------------------------------------------

    numeric_columns = []

    for col in data.columns:

        # Skip columns already detected as dates
        if col in date_columns:
            continue

        converted = pd.to_numeric(
            data[col],
            errors="coerce"
        )

        original_values = data[col].notna().sum()

        if original_values > 0:

            numeric_values = converted.notna().sum()

            # At least 70% of non-empty values
            # must be numeric
            numeric_ratio = (
                numeric_values / original_values
            )

            if numeric_ratio >= 0.70:

                data[col] = converted
                numeric_columns.append(col)

    # --------------------------------------------------
    # CATEGORICAL COLUMNS
    # --------------------------------------------------

    categorical_columns = [
        col
        for col in data.columns
        if col not in numeric_columns
        and col not in date_columns
    ]

    # ==================================================
    # LINE CHART
    # ==================================================

    st.write("### Line Chart")

    if numeric_columns:

        # ----------------------------------------------
        # DATE BASED LINE CHART
        # ----------------------------------------------

        if date_columns:

            x_column = st.selectbox(
                "Select Date / Time",
                date_columns,
                key="line_x"
            )

            y_column = st.selectbox(
                "Select Value",
                numeric_columns,
                key="line_y"
            )

            line_data = data[
                [x_column, y_column]
            ].copy()

            # Convert date
            line_data[x_column] = pd.to_datetime(
                line_data[x_column],
                errors="coerce",
                format="mixed"
            )

            # Convert value
            line_data[y_column] = pd.to_numeric(
                line_data[y_column],
                errors="coerce"
            )

            # Remove missing values
            line_data = line_data.dropna()

            # Aggregate duplicate dates
            line_data = (
                line_data
                .groupby(
                    x_column,
                    as_index=False
                )[y_column]
                .sum()
            )

            # Sort by date
            line_data = line_data.sort_values(
                by=x_column
            )

            if not line_data.empty:

                fig = px.line(
                    line_data,
                    x=x_column,
                    y=y_column,
                    markers=True,
                    title=f"{y_column} over {x_column}"
                )

                fig.update_layout(
                    xaxis_title=x_column,
                    yaxis_title=y_column,
                    hovermode="x unified"
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

        # ----------------------------------------------
        # NO DATE COLUMN
        # ----------------------------------------------

        else:

            st.info(
                "No date/time column was detected. "
                "A line chart works best with a Date, "
                "Month, Year, or other ordered column."
            )

    else:

        st.info(
            "No numeric columns available for Line Chart."
        )

    # ==================================================
    # BAR CHART
    # ==================================================

    st.write("### Bar Chart")

    # Numeric + categorical
    if (
        len(categorical_columns) >= 1
        and len(numeric_columns) >= 1
    ):

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
            data
            .groupby(
                category,
                dropna=False
            )[value]
            .sum()
            .reset_index()
            .sort_values(
                value,
                ascending=False
            )
            .head(15)
        )

        if not bar_data.empty:

            fig = px.bar(
                bar_data,
                x=category,
                y=value,
                title=f"{value} by {category}"
            )

            fig.update_layout(
                xaxis_title=category,
                yaxis_title=value
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    # Only categorical columns
    elif categorical_columns:

        category = st.selectbox(
            "Select Category",
            categorical_columns,
            key="bar_count_category"
        )

        bar_data = (
            data[category]
            .value_counts()
            .reset_index()
        )

        bar_data.columns = [
            category,
            "Count"
        ]

        bar_data = bar_data.head(15)

        fig = px.bar(
            bar_data,
            x=category,
            y="Count",
            title=f"{category} Count"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:

        st.info(
            "No suitable columns available for Bar Chart."
        )

    # ==================================================
    # PIE CHART
    # ==================================================

    st.write("### Pie Chart")

    if categorical_columns:

        pie_category = st.selectbox(
            "Select Category",
            categorical_columns,
            key="pie_category"
        )

        # ----------------------------------------------
        # CATEGORICAL + NUMERIC
        # ----------------------------------------------

        if numeric_columns:

            pie_value = st.selectbox(
                "Select Value",
                numeric_columns,
                key="pie_value"
            )

            pie_data = (
                data
                .groupby(
                    pie_category,
                    dropna=False
                )[pie_value]
                .sum()
                .reset_index()
                .sort_values(
                    pie_value,
                    ascending=False
                )
                .head(10)
            )

            if not pie_data.empty:

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

        # ----------------------------------------------
        # ONLY CATEGORICAL DATA
        # ----------------------------------------------

        else:

            pie_data = (
                data[pie_category]
                .value_counts()
                .reset_index()
            )

            pie_data.columns = [
                pie_category,
                "Count"
            ]

            pie_data = pie_data.head(10)

            if not pie_data.empty:

                fig = px.pie(
                    pie_data,
                    names=pie_category,
                    values="Count",
                    title=f"{pie_category} Distribution"
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

    else:

        st.info(
            "No categorical columns available for Pie Chart."
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

        if not scatter_data.empty:

            fig = px.scatter(
                scatter_data,
                x=x_column,
                y=y_column,
                title=f"{y_column} vs {x_column}"
            )

            fig.update_layout(
                xaxis_title=x_column,
                yaxis_title=y_column
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    else:

        st.info(
            "Scatter Plot requires at least two "
            "numeric columns."
        )

    
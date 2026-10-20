import streamlit as st
import pandas as pd
import polars as pl
import plotly.express as px

def _as_pandas(df):
    if isinstance(df, pd.DataFrame):
        return df.copy()
    if isinstance(df, pl.DataFrame):
        return df.to_pandas()
    return pd.DataFrame(df)


def _unique_column_names(columns):
    seen = {}
    result = []

    for col in columns:
        name = str(col).strip()
        if not name:
            name = "column"

        seen[name] = seen.get(name, 0) + 1
        if seen[name] > 1:
            result.append(f"{name}_{seen[name]}")
        else:
            result.append(name)

    return result


def _ensure_unique_columns(df):
    data = _as_pandas(df)
    data.columns = _unique_column_names(data.columns)
    return data


def show_visualizations(df):
    data = _ensure_unique_columns(df)

    if data.empty:
        st.info("No data available for visualization.")
        return

  
    date_columns = []
    for col in data.columns:
        if pd.api.types.is_numeric_dtype(data[col]):
            continue

        converted_date = pd.to_datetime(data[col], errors="coerce", format="mixed")
        valid_ratio = converted_date.notna().sum() / len(data) if len(data) else 0
        if valid_ratio >= 0.80:
            date_columns.append(col)

    numeric_columns = []
    for col in data.columns:
        if col in date_columns:
            continue

        converted = pd.to_numeric(data[col], errors="coerce")
        original_values = data[col].notna().sum()
        if original_values > 0:
            numeric_ratio = converted.notna().sum() / original_values
            if numeric_ratio >= 0.70:
                data[col] = converted
                numeric_columns.append(col)

    categorical_columns = [
        col for col in data.columns
        if col not in numeric_columns and col not in date_columns
    ]

    st.write("### Line Chart")
    if numeric_columns and date_columns:
        x_column = st.selectbox("Select Date / Time", date_columns, key="line_x")
        y_column = st.selectbox("Select Value", numeric_columns, key="line_y")

        line_data = data[[x_column, y_column]].copy()
        line_data[x_column] = pd.to_datetime(line_data[x_column], errors="coerce", format="mixed")
        line_data[y_column] = pd.to_numeric(line_data[y_column], errors="coerce")
        line_data = line_data.dropna()
        line_data = line_data.groupby(x_column, as_index=False)[y_column].sum()
        line_data = line_data.sort_values(by=x_column)

        if not line_data.empty:
            fig = px.line(
                line_data,
                x=x_column,
                y=y_column,
                markers=True,
                title=f"{y_column} over {x_column}",
            )
            fig.update_layout(xaxis_title=x_column, yaxis_title=y_column, hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No suitable date/value columns available for Line Chart.")

    st.write("### Bar Chart")
    if len(categorical_columns) >= 1 and len(numeric_columns) >= 1:
        category = st.selectbox("Select Category", categorical_columns, key="bar_category")
        value = st.selectbox("Select Value", numeric_columns, key="bar_value")

        bar_data = (
            data.groupby(category, dropna=False)[value]
            .sum()
            .reset_index()
            .sort_values(value, ascending=False)
            .head(15)
        )

        if not bar_data.empty:
            fig = px.bar(bar_data, x=category, y=value, title=f"{value} by {category}")
            fig.update_layout(xaxis_title=category, yaxis_title=value)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No suitable columns available for Bar Chart.")

    st.write("### Pie Chart")
    if categorical_columns:
        pie_category = st.selectbox("Select Category", categorical_columns, key="pie_category")

        if numeric_columns:
            pie_value = st.selectbox("Select Value", numeric_columns, key="pie_value")
            pie_data = (
                data.groupby(pie_category, dropna=False)[pie_value]
                .sum()
                .reset_index()
                .sort_values(pie_value, ascending=False)
                .head(10)
            )
            if not pie_data.empty:
                fig = px.pie(pie_data, names=pie_category, values=pie_value, title=f"{pie_value} Distribution")
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No categorical columns available for Pie Chart.")

    st.write("### Scatter Plot")
    numeric_cols = data.select_dtypes(include="number").columns.tolist()

    if len(numeric_cols) >= 2:
        x_col = st.selectbox("Select X-axis column", numeric_cols, index=0, key="scatter_x")
        y_options = [col for col in numeric_cols if col != x_col]
        y_col = st.selectbox("Select Y-axis column", y_options, index=0, key="scatter_y")

        fig = px.scatter(
            data,
            x=x_col,
            y=y_col,
            title=f"{y_col} vs {x_col}",
            hover_data=[c for c in data.columns if c not in [x_col, y_col]],
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Scatter plot requires at least two numerical columns.")

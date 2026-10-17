import streamlit as st
import pandas as pd
import plotly.express as px
import polars as pl


def _as_pandas(df):
    if isinstance(df, pd.DataFrame):
        return df.copy()
    if isinstance(df, pl.DataFrame):
        return df.to_pandas()
    return pd.DataFrame(df)


def make_unique_columns(df):
    """Make all column names unique, including repeated empty names."""
    df = df.copy()
    new_columns = []
    seen = set()

    for column in df.columns:
        name = str(column).strip()

        if not name:
            name = "Unnamed"

        candidate = name
        counter = 1

        while candidate in seen:
            candidate = f"{name}_{counter}"
            counter += 1

        new_columns.append(candidate)
        seen.add(candidate)

    df.columns = new_columns
    return df


def show_dashboard(dataframe, dataset_name):
    st.title(f"{dataset_name} Dashboard")
    st.caption(f"Dataset: {dataset_name}")

    if dataframe is None or dataframe.empty:
        st.warning(
            "No dataset available. Return to the preview page and upload a file."
        )
        return

    # Fix duplicate column names before using Plotly or pandas.
    dataframe = make_unique_columns(dataframe)

    # Identify columns automatically.
    columns = list(dataframe.columns)
    numeric_cols = dataframe.select_dtypes(include="number").columns.tolist()

    def find_column(keywords, excluded=None):
        excluded = excluded or []

        for col in columns:
            name = str(col).lower().replace("_", " ")

            if col not in excluded and any(
                word in name for word in keywords
            ):
                return col

        return None

    product_col = find_column([
        "product name", "product", "item description",
        "item name", "sku"
    ])

    category_col = find_column([
        "category", "item type", "product type"
    ])

    sales_col = find_column([
        "total sales", "sales", "revenue",
        "retail sales", "amount"
    ])

    quantity_col = find_column([
        "quantity", "qty", "units sold"
    ])

    date_col = find_column(["date", "month", "year"])

    if sales_col not in numeric_cols if sales_col else True:
        sales_col = None

    if quantity_col not in numeric_cols if quantity_col else True:
        quantity_col = None

    # Detect numeric columns if names were not recognized.
    if sales_col is None and numeric_cols:
        sales_col = numeric_cols[0]

    if quantity_col is None:
        quantity_col = next(
            (col for col in numeric_cols if col != sales_col),
            None
        )

    if product_col is None:
        product_col = category_col

    # Parse a usable date column.
    parsed_date_col = None

    if date_col:
        parsed = pd.to_datetime(dataframe[date_col], errors="coerce")

        if parsed.notna().sum() > 0:
            dataframe["_Dashboard_Date"] = parsed
            parsed_date_col = "_Dashboard_Date"

    st.subheader("Filters")

    filter_cols = st.columns(3)
    filtered = dataframe.copy()

    # Date/year filter.
    if parsed_date_col:
        valid_dates = filtered[parsed_date_col].dropna()

        if not valid_dates.empty:
            years = sorted(valid_dates.dt.year.unique().tolist())

            with filter_cols[0]:
                selected_years = st.multiselect(
                    "Year",
                    years,
                    default=years,
                    key="dashboard_years"
                )

            filtered = filtered[
                filtered[parsed_date_col].isna()
                | filtered[parsed_date_col].dt.year.isin(selected_years)
            ]

    # Category filter.
    if category_col:
        category_values = sorted(
            filtered[category_col]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        with filter_cols[1]:
            selected_categories = st.multiselect(
                "Category",
                category_values,
                default=category_values,
                key="dashboard_categories"
            )

        filtered = filtered[
            filtered[category_col].isna()
            | filtered[category_col].astype(str).isin(
                selected_categories
            )
        ]

    # Product filter.
    if product_col and product_col != category_col:
        product_values = sorted(
            filtered[product_col]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        with filter_cols[2]:
            selected_products = st.multiselect(
                "Product",
                product_values,
                default=product_values,
                key="dashboard_products"
            )

        filtered = filtered[
            filtered[product_col].isna()
            | filtered[product_col].astype(str).isin(
                selected_products
            )
        ]

    st.divider()

    # Four KPI cards.
    total_records = len(filtered)

    unique_products = (
        filtered[product_col].nunique()
        if product_col else 0
    )

    total_sales = (
        pd.to_numeric(
            filtered[sales_col], errors="coerce"
        ).sum()
        if sales_col else 0
    )

    average_quantity = (
        pd.to_numeric(
            filtered[quantity_col], errors="coerce"
        ).mean()
        if quantity_col else float("nan")
    )

    k1, k2, k3, k4 = st.columns(4)

    k1.metric("Total Records", f"{total_records:,}")
    k2.metric("Unique Products", f"{unique_products:,}")
    k3.metric("Total Sales", f"{total_sales:,.2f}")
    k4.metric(
        "Average Quantity",
        f"{average_quantity:,.2f}"
        if pd.notna(average_quantity) else "N/A"
    )

    st.divider()

    # Chart 1: Sales by product/category.
    left, right = st.columns(2)

    with left:
        st.subheader("Sales by Product / Category")

        bar_group = product_col or category_col

        if sales_col and bar_group:
            bar_data = filtered.copy()

            bar_data[sales_col] = pd.to_numeric(
                bar_data[sales_col], errors="coerce"
            )

            bar_data = (
                bar_data.groupby(
                    bar_group, dropna=False, as_index=False
                )[sales_col]
                .sum()
                .sort_values(sales_col, ascending=False)
                .head(15)
            )

            fig = px.bar(
                bar_data,
                x=bar_group,
                y=sales_col,
                title="Top 15 by Sales"
            )

            st.plotly_chart(fig, use_container_width=True)

        else:
            st.info(
                "A product/category column and numeric sales column are needed."
            )

    # Chart 2: Sales trend.
    with right:
        st.subheader("Sales Trend")

        if sales_col and parsed_date_col:
            trend = filtered.copy()

            trend[sales_col] = pd.to_numeric(
                trend[sales_col], errors="coerce"
            )

            trend = trend.dropna(subset=[parsed_date_col])
            trend["Period"] = (
                trend[parsed_date_col]
                .dt.to_period("M")
                .astype(str)
            )

            trend = (
                trend.groupby(
                    "Period", as_index=False
                )[sales_col]
                .sum()
                .sort_values("Period")
            )

            fig = px.line(
                trend,
                x="Period",
                y=sales_col,
                markers=True,
                title="Sales Over Time"
            )

            st.plotly_chart(fig, use_container_width=True)

        else:
            st.info(
                "A usable date and numeric sales column are needed."
            )

    # Chart 3: Sales share.
    with left:
        st.subheader("Sales Share")

        pie_group = category_col or product_col

        if sales_col and pie_group:
            pie_data = filtered.copy()

            pie_data[sales_col] = pd.to_numeric(
                pie_data[sales_col], errors="coerce"
            )

            pie_data = (
                pie_data.groupby(
                    pie_group, dropna=False, as_index=False
                )[sales_col]
                .sum()
                .nlargest(10, sales_col)
            )

            # Exclude non-positive values from the pie chart.
            pie_data = pie_data[pie_data[sales_col] > 0]

            if not pie_data.empty:
                fig = px.pie(
                    pie_data,
                    names=pie_group,
                    values=sales_col,
                    title="Sales Share by Category"
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No positive sales values are available.")

        else:
            st.info(
                "A category/product column and numeric sales column are needed."
            )

    # Chart 4: Sales versus quantity.
    with right:
        st.subheader("Sales vs Quantity")

        if sales_col and quantity_col:
            scatter_data = filtered.copy()

            scatter_data[sales_col] = pd.to_numeric(
                scatter_data[sales_col], errors="coerce"
            )

            scatter_data[quantity_col] = pd.to_numeric(
                scatter_data[quantity_col], errors="coerce"
            )

            scatter_data = scatter_data.dropna(
                subset=[sales_col, quantity_col]
            )

            if not scatter_data.empty:
                hover_columns = (
                    [product_col]
                    if product_col and product_col not in [
                        sales_col, quantity_col
                    ]
                    else None
                )

                fig = px.scatter(
                    scatter_data,
                    x=quantity_col,
                    y=sales_col,
                    title="Sales vs Quantity",
                    hover_data=hover_columns
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No valid sales and quantity values to plot.")

        else:
            st.info(
                "Two suitable numeric columns are needed for the scatter plot."
            )

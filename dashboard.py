import pandas as pd
import streamlit as st
import plotly.express as px


def _as_pandas(df):
    if isinstance(df, pd.DataFrame):
        return df.copy()
    return pd.DataFrame(df)


def make_safe_columns(df):
    df = df.copy()
    seen = {}
    new_cols = []

    for col in df.columns:
        name = str(col).strip() or "Unnamed"
        base = name
        idx = 1
        while name in seen:
            name = f"{base}_{idx}"
            idx += 1
        seen[name] = True
        new_cols.append(name)

    df.columns = new_cols
    return df


def clean_dataset_name(name):
    if not name:
        return "Dataset"
    clean_name = name.rsplit(".", 1)[0] if "." in name else name
    clean_name = clean_name.replace(" (1)", "").replace(" (2)", "").replace(" (3)", "")
    return clean_name


def detect_product_column(df):
    keywords = [
        "product", "item", "sku", "productname", "product_name",
        "itemname", "item_name", "title", "name"
    ]

    for col in df.columns:
        col_lower = str(col).strip().lower().replace(" ", "")
        for kw in keywords:
            if col_lower == kw or kw in col_lower:
                return col

    for col in df.columns:
        if df[col].dtype == "object" and df[col].nunique(dropna=True) <= 200:
            return col

    return None


def detect_numeric_metric(df):
    metric_candidates = [
        "sales", "revenue", "amount", "price", "total", "quantity",
        "qty", "units", "count"
    ]

    for col in df.columns:
        col_lower = str(col).strip().lower().replace(" ", "")
        for kw in metric_candidates:
            if kw in col_lower and pd.api.types.is_numeric_dtype(df[col]):
                return col

    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            return col

    return None


def detect_category_column(df):
    for col in df.columns:
        if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_categorical_dtype(df[col]):
            unique_count = df[col].dropna().nunique()
            if 1 < unique_count <= 20:
                return col
    return None


def detect_date_column(df):
    for col in df.columns:
        try:
            parsed = pd.to_datetime(df[col], errors="coerce")
            ratio = parsed.notna().mean()
            if ratio > 0.7:
                return col
        except Exception:
            pass
    return None


def get_filter_columns(df):
    candidate_cols = []

    for col in df.columns:
        if col.lower() in {"id", "index", "rowid", "customerid", "productid"}:
            continue

        if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_categorical_dtype(df[col]):
            unique_count = df[col].dropna().nunique()
            if 2 <= unique_count <= 50:
                candidate_cols.append(col)
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            candidate_cols.append(col)

    if len(candidate_cols) >= 2:
        return candidate_cols[:2]

    fallback = []
    for col in df.columns:
        if col.lower() in {"id", "index", "rowid", "customerid", "productid"}:
            continue
        if not pd.api.types.is_numeric_dtype(df[col]):
            fallback.append(col)
        if len(fallback) == 2:
            break

    return fallback[:2]


def get_bar_group_columns(df):
    cols = []
    for col in df.columns:
        if col.lower() in {"id", "index", "rowid", "customerid", "productid"}:
            continue

        if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_categorical_dtype(df[col]):
            cols.append(col)
        elif not pd.api.types.is_numeric_dtype(df[col]):
            cols.append(col)

    return cols[:10]


def get_numeric_metric_columns(df):
    excluded = {"id", "index", "rowid", "customerid", "productid", "customer_id", "orderid"}
    cols = []

    for col in df.columns:
        name = str(col).strip().lower()
        if name in excluded:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            cols.append(col)

    return cols


def show_dashboard(df, dataset_name):
    if df is None or df.empty:
        st.warning("No dataset available for the dashboard.")
        return

    df = _as_pandas(df)
    df = make_safe_columns(df)
    df = df.copy()

    clean_name = clean_dataset_name(dataset_name)
    st.title(f"{clean_name} Dashboard")

    st.markdown("### KPI Overview")

    product_col = detect_product_column(df)
    metric_col = detect_numeric_metric(df)
    category_col = detect_category_column(df)
    date_col = detect_date_column(df)

    filtered_df = df.copy()

    total_records = len(filtered_df)
    unique_records = filtered_df[product_col].nunique(dropna=True) if product_col else total_records

    c1, c2 = st.columns(2)
    c1.metric("Total Records", f"{total_records:,}")
    c2.metric("Unique Records", f"{unique_records:,}")

    filter_columns = get_filter_columns(df)
    if filter_columns:
        st.subheader("Dashboard Filters")
        cols = st.columns(min(len(filter_columns), 2))
        selected_values = {}

        for i, col in enumerate(filter_columns):
            options = sorted(df[col].dropna().astype(str).unique().tolist())
            selected = cols[i % 2].multiselect(
                f"{col}",
                options=options,
                default=[],
                key=f"dashboard_filter_{col}"
            )
            selected_values[col] = selected

        for col, vals in selected_values.items():
            if vals:
                filtered_df = filtered_df[filtered_df[col].astype(str).isin(vals)]

        total_records = len(filtered_df)
        unique_records = filtered_df[product_col].nunique(dropna=True) if product_col else total_records

        c1, c2 = st.columns(2)
        c1.metric("Total Records", f"{total_records:,}")
        c2.metric("Unique Records", f"{unique_records:,}")

        bar_group_columns = get_bar_group_columns(filtered_df)
        if bar_group_columns:
            selected_bar_col = cols[0].selectbox(
                "Bar Chart By",
                options=bar_group_columns,
                index=0,
                key="bar_chart_group"
            )
        else:
            selected_bar_col = None
    else:
        st.info("No filter options available for this dataset.")
        selected_bar_col = None

    charts = []

    if selected_bar_col is None:
        fallback_cols = []
        for col in filtered_df.columns:
            if col.lower() in {"id", "index", "rowid", "customerid", "productid"}:
                continue
            if not pd.api.types.is_numeric_dtype(filtered_df[col]):
                fallback_cols.append(col)
        selected_bar_col = fallback_cols[0] if fallback_cols else None

    if selected_bar_col is not None:
        bar_df = filtered_df[[selected_bar_col]].copy()
        bar_df[selected_bar_col] = bar_df[selected_bar_col].fillna("Unknown")
        bar_df.columns = ["Category"]

        bar_df = (
            bar_df.groupby("Category", dropna=False)
            .size()
            .reset_index(name="Count")
            .sort_values("Count", ascending=False)
            .head(10)
        )

        if not bar_df.empty:
            charts.append(("Bar Chart", "Category Distribution", bar_df, "Category", "Count"))

            pie_df = bar_df.head(8).copy()
            charts.append(("Pie Chart", "Category Share", pie_df, "Category", "Count"))

    if len(charts) == 0:
        st.info("No meaningful chart could be generated for this dataset.")
        return

    display_charts = charts[:2]

    st.markdown("### Charts")

    for chart_type, chart_title, chart_df, x_col, y_col in display_charts:
        st.subheader(chart_title)

        if chart_type == "Bar Chart":
            if x_col in chart_df.columns and y_col in chart_df.columns:
                st.bar_chart(chart_df, x=x_col, y=y_col, use_container_width=True)

        elif chart_type == "Pie Chart":
            if x_col in chart_df.columns and y_col in chart_df.columns:
                st.plotly_chart(
                    px.pie(chart_df, names=x_col, values=y_col, title=chart_title),
                    use_container_width=True
                )

import streamlit as st
from dashboard import show_dashboard
import os

st.set_page_config(
    page_title="Retail Dashboard",
    page_icon="📊",
    layout="wide"
)

if st.button("← Back to Dataset Preview"):
    st.switch_page("app.py")

cleaned_data = st.session_state.get("cleaned_df")
dataset_name = st.session_state.get("dataset_name", "Uploaded Dataset")

if cleaned_data is None:
    st.warning("No dataset found. Return to the main page and upload a dataset.")
else:
    clean_name = os.path.splitext(os.path.basename(dataset_name))[0]
    clean_name = clean_name.replace(" (1)", "").replace(" (2)", "")
    show_dashboard(cleaned_data, dataset_name)

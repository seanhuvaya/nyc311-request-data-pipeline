from pathlib import Path
import sys

import pandas as pd
import streamlit as st
import streamlit_shadcn_ui as ui

sys.path.append(str(Path(__file__).resolve().parents[1]))

from api_client import ApiClientError, get_configured_base_url, get_requests_by_complaint_type
from ui import apply_shadcn_theme, metric_cards, page_header, section_heading


st.set_page_config(page_title="Complaint Type Analysis", layout="wide")
apply_shadcn_theme()
page_header(
    title="Complaint Type Analysis",
    description="Top complaint categories with totals and resolution indicators.",
    source=f"{get_configured_base_url()}/api/v1/requests/by-complaint-type",
)


@st.cache_data(ttl=300)
def load_complaint_data() -> pd.DataFrame:
    data = get_requests_by_complaint_type()
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    if "request_date" in df.columns:
        df["request_date"] = pd.to_datetime(df["request_date"], errors="coerce")
    return df


try:
    df = load_complaint_data()
except ApiClientError as exc:
    st.error(str(exc))
    st.stop()

if df.empty:
    st.warning("No complaint-type records returned by the API.")
    st.stop()

available_dates = sorted([d for d in df["request_date"].dropna().unique()]) if "request_date" in df.columns else []
if available_dates:
    date_options = [str(pd.Timestamp(d).date()) for d in available_dates]
    selected_date_str = ui.select(
        label="Request Date",
        options=date_options,
        key="complaint-date-select",
    )
    selected_date = pd.Timestamp(selected_date_str) if selected_date_str else available_dates[-1]
    filtered = df[df["request_date"] == selected_date].copy()
else:
    filtered = df.copy()

top_n = ui.slider(
    default_value=15,
    min_value=5,
    max_value=50,
    step=5,
    label="Top N complaint types",
    key="top-n-slider",
)
if "total_requests" in filtered.columns:
    filtered = filtered.sort_values("total_requests", ascending=False).head(top_n)

metrics = [{"title": "Complaint Types", "value": len(filtered), "description": "rows in selected slice"}]
if "total_requests" in filtered.columns:
    metrics.append(
        {"title": "Total Requests (Top N)", "value": int(filtered["total_requests"].sum()), "description": "sum for displayed complaint types"}
    )
if "closed_requests" in filtered.columns:
    metrics.append(
        {"title": "Closed Requests (Top N)", "value": int(filtered["closed_requests"].sum()), "description": "closed requests in displayed set"}
    )
metric_cards(metrics, key_prefix="complaint-page-metrics")

if "complaint_type" in filtered.columns and "total_requests" in filtered.columns:
    chart_data = filtered.set_index("complaint_type")[["total_requests"]]
    section_heading("Total Requests by Complaint Type")
    st.bar_chart(chart_data, use_container_width=True)

if all(col in filtered.columns for col in ("complaint_type", "avg_resolution_time_in_hours")):
    res_df = filtered[["complaint_type", "avg_resolution_time_in_hours"]].set_index("complaint_type")
    section_heading("Average Resolution Time (Hours)")
    st.bar_chart(res_df, use_container_width=True)

section_heading("Complaint-Type Data")
st.dataframe(filtered, use_container_width=True, height=420)

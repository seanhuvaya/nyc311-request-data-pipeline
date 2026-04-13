from pathlib import Path
import sys

import pandas as pd
import streamlit as st
import streamlit_shadcn_ui as ui

sys.path.append(str(Path(__file__).resolve().parents[1]))

from api_client import ApiClientError, get_configured_base_url, get_requests
from ui import apply_shadcn_theme, metric_cards, page_header, section_heading


st.set_page_config(page_title="Raw Requests", layout="wide")
apply_shadcn_theme()
page_header(
    title="Raw Requests",
    description="Filterable records and request-level status metrics.",
    source=f"{get_configured_base_url()}/api/v1/requests/",
)


@st.cache_data(ttl=300)
def load_requests() -> pd.DataFrame:
    data = get_requests()
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)

    for col in ("created_date", "closed_date"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    return df


try:
    df = load_requests()
except ApiClientError as exc:
    st.error(str(exc))
    st.stop()

if df.empty:
    st.warning("No records returned by the API.")
    st.stop()

with st.sidebar:
    ui.card(
        title="Filters",
        content="Narrow the request set for this view.",
        description="Selections update metrics and table below.",
        key="raw-sidebar-filters",
    )
    boroughs = sorted([b for b in df.get("borough", pd.Series(dtype="object")).dropna().unique()])
    complaint_types = sorted(
        [c for c in df.get("complaint_type", pd.Series(dtype="object")).dropna().unique()]
    )
    statuses = sorted([s for s in df.get("status", pd.Series(dtype="object")).dropna().unique()])

    selected_boroughs = st.multiselect("Borough", boroughs, default=boroughs)
    selected_complaint_types = st.multiselect(
        "Complaint Type", complaint_types, default=complaint_types[:20] if complaint_types else []
    )
    selected_statuses = st.multiselect("Status", statuses, default=statuses)

filtered = df.copy()
if selected_boroughs and "borough" in filtered.columns:
    filtered = filtered[filtered["borough"].isin(selected_boroughs)]
if selected_complaint_types and "complaint_type" in filtered.columns:
    filtered = filtered[filtered["complaint_type"].isin(selected_complaint_types)]
if selected_statuses and "status" in filtered.columns:
    filtered = filtered[filtered["status"].isin(selected_statuses)]

metrics = [{"title": "Rows", "value": len(filtered), "description": "records after filtering"}]
if "is_closed" in filtered.columns:
    closed_count = int(filtered["is_closed"].fillna(False).sum())
    metrics.extend(
        [
            {"title": "Closed Requests", "value": closed_count, "description": "records marked closed"},
            {"title": "Open Requests", "value": len(filtered) - closed_count, "description": "active records"},
        ]
    )
metric_cards(metrics, key_prefix="raw-page-metrics")

section_heading("Request Sample", "Live response rows from the API.")
st.dataframe(filtered, use_container_width=True, height=520)

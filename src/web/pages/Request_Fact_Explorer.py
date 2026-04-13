from pathlib import Path
import sys

import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))

from api_client import ApiClientError, get_configured_base_url, get_request_fact
from ui import apply_shadcn_theme, metric_cards, page_header, section_heading


st.set_page_config(page_title="Request Fact Explorer", layout="wide")
apply_shadcn_theme()
page_header(
    title="Request Fact Explorer",
    description="Request-level gold fact table for detailed drill-down analysis.",
    source=f"{get_configured_base_url()}/api/v1/requests/request-fact",
)

start_date = st.date_input("Start Date", value=None, key="fact-start")
end_date = st.date_input("End Date", value=None, key="fact-end")
agency = st.text_input("Agency (optional)", value="", key="fact-agency")
borough = st.text_input("Borough (optional)", value="", key="fact-borough")
complaint_type = st.text_input("Complaint Type (optional)", value="", key="fact-complaint")


@st.cache_data(ttl=300)
def load_data(
    start_date_value: str | None,
    end_date_value: str | None,
    agency_value: str,
    borough_value: str,
    complaint_value: str,
) -> pd.DataFrame:
    data = get_request_fact(
        start_date=start_date_value,
        end_date=end_date_value,
        agency=agency_value or None,
        borough=borough_value or None,
        complaint_type=complaint_value or None,
    )
    return pd.DataFrame(data) if data else pd.DataFrame()


try:
    df = load_data(
        start_date.isoformat() if start_date else None,
        end_date.isoformat() if end_date else None,
        agency,
        borough,
        complaint_type,
    )
except ApiClientError as exc:
    st.error(str(exc))
    st.stop()

if df.empty:
    st.warning("No request fact records returned by the API.")
    st.stop()

if "created_date" in df.columns:
    df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce")
if "is_closed" in df.columns:
    df["is_closed"] = df["is_closed"].fillna(False)

closed_count = int(df["is_closed"].sum()) if "is_closed" in df.columns else 0
metric_cards(
    [
        {"title": "Rows", "value": len(df), "description": "request-level records"},
        {"title": "Closed", "value": closed_count, "description": "requests marked closed"},
        {"title": "Open", "value": len(df) - closed_count, "description": "requests still open"},
    ],
    key_prefix="fact-metrics",
)

section_heading("Requests Created Over Time")
if "created_date" in df.columns:
    daily_counts = df.groupby(df["created_date"].dt.date)["unique_key"].count()
    st.line_chart(daily_counts, use_container_width=True)

section_heading("Data")
st.dataframe(df, use_container_width=True, height=500)

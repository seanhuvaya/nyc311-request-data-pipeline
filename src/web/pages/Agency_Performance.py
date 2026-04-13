from pathlib import Path
import sys

import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))

from api_client import ApiClientError, get_configured_base_url, get_requests_by_agency_daily
from ui import apply_shadcn_theme, metric_cards, page_header, section_heading


st.set_page_config(page_title="Agency Performance", layout="wide")
apply_shadcn_theme()
page_header(
    title="Agency Performance",
    description="Daily operational workload and closure performance by agency.",
    source=f"{get_configured_base_url()}/api/v1/requests/by-agency-daily",
)

start_date = st.date_input("Start Date", value=None)
end_date = st.date_input("End Date", value=None)
agency = st.text_input("Agency (optional)", value="")


@st.cache_data(ttl=300)
def load_data(start_date_value: str | None, end_date_value: str | None, agency_value: str) -> pd.DataFrame:
    data = get_requests_by_agency_daily(
        start_date=start_date_value,
        end_date=end_date_value,
        agency=agency_value or None,
    )
    return pd.DataFrame(data) if data else pd.DataFrame()


try:
    df = load_data(
        start_date.isoformat() if start_date else None,
        end_date.isoformat() if end_date else None,
        agency,
    )
except ApiClientError as exc:
    st.error(str(exc))
    st.stop()

if df.empty:
    st.warning("No agency performance records returned by the API.")
    st.stop()

if "request_date" in df.columns:
    df["request_date"] = pd.to_datetime(df["request_date"], errors="coerce")
    df = df.sort_values("request_date")

metric_cards(
    [
        {"title": "Rows", "value": len(df), "description": "records returned"},
        {"title": "Agencies", "value": df["agency"].nunique(), "description": "unique agencies"},
        {"title": "Total Requests", "value": int(pd.to_numeric(df["total_requests"], errors="coerce").sum()),
         "description": "sum over filtered period"},
    ],
    key_prefix="agency-metrics",
)

section_heading("Daily Requests by Agency")
chart_df = df.pivot_table(index="request_date", columns="agency", values="total_requests", aggfunc="sum")
st.line_chart(chart_df, use_container_width=True)

section_heading("Data")
st.dataframe(df, use_container_width=True, height=450)

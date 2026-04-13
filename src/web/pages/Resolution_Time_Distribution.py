from pathlib import Path
import sys

import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))

from api_client import ApiClientError, get_configured_base_url, get_resolution_time_distribution
from ui import apply_shadcn_theme, metric_cards, page_header, section_heading


st.set_page_config(page_title="Resolution Time Distribution", layout="wide")
apply_shadcn_theme()
page_header(
    title="Resolution Time Distribution",
    description="Monthly request counts grouped by resolution-time buckets.",
    source=f"{get_configured_base_url()}/api/v1/requests/resolution-time-distribution",
)

start_date = st.date_input("Start Month", value=None, key="dist-start")
end_date = st.date_input("End Month", value=None, key="dist-end")
agency = st.text_input("Agency (optional)", value="", key="dist-agency")
complaint_type = st.text_input("Complaint Type (optional)", value="", key="dist-complaint")


@st.cache_data(ttl=300)
def load_data(
    start_date_value: str | None,
    end_date_value: str | None,
    agency_value: str,
    complaint_value: str,
) -> pd.DataFrame:
    data = get_resolution_time_distribution(
        start_date=start_date_value,
        end_date=end_date_value,
        agency=agency_value or None,
        complaint_type=complaint_value or None,
    )
    return pd.DataFrame(data) if data else pd.DataFrame()


try:
    df = load_data(
        start_date.isoformat() if start_date else None,
        end_date.isoformat() if end_date else None,
        agency,
        complaint_type,
    )
except ApiClientError as exc:
    st.error(str(exc))
    st.stop()

if df.empty:
    st.warning("No resolution distribution records returned by the API.")
    st.stop()

df["request_month"] = pd.to_datetime(df["request_month"], errors="coerce")
df = df.sort_values(["request_month", "resolution_bucket"])

metric_cards(
    [
        {"title": "Rows", "value": len(df), "description": "records returned"},
        {"title": "Buckets", "value": df["resolution_bucket"].nunique(), "description": "bucket categories"},
        {"title": "Requests", "value": int(pd.to_numeric(df["request_count"], errors="coerce").sum()),
         "description": "total requests in result"},
    ],
    key_prefix="resolution-dist-metrics",
)

section_heading("Bucket Trends")
chart_df = df.pivot_table(index="request_month", columns="resolution_bucket", values="request_count", aggfunc="sum")
st.area_chart(chart_df, use_container_width=True)

section_heading("Data")
st.dataframe(df, use_container_width=True, height=450)

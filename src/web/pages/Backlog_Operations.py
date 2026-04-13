from pathlib import Path
import sys

import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))

from api_client import ApiClientError, get_configured_base_url, get_open_backlog_daily
from ui import apply_shadcn_theme, metric_cards, page_header, section_heading


st.set_page_config(page_title="Backlog Operations", layout="wide")
apply_shadcn_theme()
page_header(
    title="Backlog Operations",
    description="Open backlog snapshot counts and aging trends by operational segment.",
    source=f"{get_configured_base_url()}/api/v1/requests/open-backlog-daily",
)

start_date = st.date_input("Start Date", value=None, key="backlog-start")
end_date = st.date_input("End Date", value=None, key="backlog-end")
agency = st.text_input("Agency (optional)", value="", key="backlog-agency")
borough = st.text_input("Borough (optional)", value="", key="backlog-borough")
complaint_type = st.text_input("Complaint Type (optional)", value="", key="backlog-complaint")


@st.cache_data(ttl=300)
def load_data(
    start_date_value: str | None,
    end_date_value: str | None,
    agency_value: str,
    borough_value: str,
    complaint_type_value: str,
) -> pd.DataFrame:
    data = get_open_backlog_daily(
        start_date=start_date_value,
        end_date=end_date_value,
        agency=agency_value or None,
        borough=borough_value or None,
        complaint_type=complaint_type_value or None,
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
    st.warning("No backlog records returned by the API.")
    st.stop()

df["snapshot_date"] = pd.to_datetime(df["snapshot_date"], errors="coerce")
df = df.sort_values("snapshot_date")

metric_cards(
    [
        {"title": "Rows", "value": len(df), "description": "records returned"},
        {"title": "Open Backlog", "value": int(pd.to_numeric(df["open_backlog_count"], errors="coerce").sum()),
         "description": "sum of open items"},
        {"title": "Max Age (hrs)", "value": f"{pd.to_numeric(df['max_age_open_hours'], errors='coerce').max():.1f}",
         "description": "oldest open issue in result"},
    ],
    key_prefix="backlog-metrics",
)

section_heading("Backlog Trend")
backlog_series = df.groupby("snapshot_date")["open_backlog_count"].sum()
st.line_chart(backlog_series, use_container_width=True)

section_heading("Data")
st.dataframe(df, use_container_width=True, height=450)

from pathlib import Path
import sys

import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))

from api_client import ApiClientError, get_configured_base_url, get_sla_performance_daily
from ui import apply_shadcn_theme, metric_cards, page_header, section_heading


st.set_page_config(page_title="SLA Performance", layout="wide")
apply_shadcn_theme()
page_header(
    title="SLA Performance",
    description="Closure timeliness by day, agency, and complaint type.",
    source=f"{get_configured_base_url()}/api/v1/requests/sla-performance-daily",
)

start_date = st.date_input("Start Date", value=None, key="sla-start")
end_date = st.date_input("End Date", value=None, key="sla-end")
agency = st.text_input("Agency (optional)", value="", key="sla-agency")
complaint_type = st.text_input("Complaint Type (optional)", value="", key="sla-complaint")


@st.cache_data(ttl=300)
def load_data(start_date_value: str | None, end_date_value: str | None, agency_value: str, complaint_value: str) -> pd.DataFrame:
    data = get_sla_performance_daily(
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
    st.warning("No SLA performance records returned by the API.")
    st.stop()

df["request_date"] = pd.to_datetime(df["request_date"], errors="coerce")
df = df.sort_values("request_date")

metric_cards(
    [
        {"title": "Closed Requests", "value": int(pd.to_numeric(df["total_closed_requests"], errors="coerce").sum()),
         "description": "total closed in result"},
        {"title": "Avg <=24h", "value": f"{(pd.to_numeric(df['pct_closed_within_24h'], errors='coerce').mean() * 100):.1f}%",
         "description": "average same-day close rate"},
        {"title": "Avg <=72h", "value": f"{(pd.to_numeric(df['pct_closed_within_72h'], errors='coerce').mean() * 100):.1f}%",
         "description": "average 72-hour close rate"},
    ],
    key_prefix="sla-metrics",
)

section_heading("SLA Trend")
trend_df = df.groupby("request_date")[["closed_within_24h", "closed_within_72h", "closed_after_72h"]].sum()
st.line_chart(trend_df, use_container_width=True)

section_heading("Data")
st.dataframe(df, use_container_width=True, height=450)

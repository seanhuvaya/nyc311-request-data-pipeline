from pathlib import Path
import sys

import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))

from api_client import ApiClientError, get_configured_base_url, get_requests_daily
from ui import apply_shadcn_theme, metric_cards, page_header, section_heading


st.set_page_config(page_title="Daily Trends", layout="wide")
apply_shadcn_theme()
page_header(
    title="Daily Trends",
    description="Daily totals, closure performance, and resolution-time trends.",
    source=f"{get_configured_base_url()}/api/v1/requests/daily",
)


@st.cache_data(ttl=300)
def load_daily() -> pd.DataFrame:
    data = get_requests_daily()
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    if "request_date" in df.columns:
        df["request_date"] = pd.to_datetime(df["request_date"], errors="coerce")
        df = df.sort_values("request_date")
        df = df.set_index("request_date")
    return df


try:
    df = load_daily()
except ApiClientError as exc:
    st.error(str(exc))
    st.stop()

if df.empty:
    st.warning("No daily trend records returned by the API.")
    st.stop()

metrics = []
if "total_requests" in df.columns:
    metrics.append(
        {
            "title": "Latest Total Requests",
            "value": int(df["total_requests"].iloc[-1]),
            "description": "most recent daily total",
        }
    )
if "pct_closed" in df.columns:
    metrics.append(
        {
            "title": "Latest Close Rate",
            "value": f"{float(df['pct_closed'].iloc[-1]) * 100:.1f}%",
            "description": "share of daily requests closed",
        }
    )
if "avg_resolution_time_in_hours" in df.columns:
    val = df["avg_resolution_time_in_hours"].iloc[-1]
    metrics.append(
        {
            "title": "Latest Avg Resolution (hrs)",
            "value": f"{float(val):.1f}" if pd.notna(val) else "N/A",
            "description": "mean resolution time",
        }
    )
metric_cards(metrics, key_prefix="daily-page-metrics")

section_heading("Request Volume Over Time")
volume_cols = [c for c in ("total_requests", "open_requests", "closed_requests") if c in df.columns]
if volume_cols:
    st.line_chart(df[volume_cols], use_container_width=True)

section_heading("Closure Rate Trend")
if "pct_closed" in df.columns:
    st.line_chart(df[["pct_closed"]], use_container_width=True)

section_heading("Daily Data")
st.dataframe(df.reset_index(), use_container_width=True, height=420)

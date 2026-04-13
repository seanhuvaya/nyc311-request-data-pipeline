from pathlib import Path
import sys

import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))

from api_client import ApiClientError, get_configured_base_url, get_top_complaints_monthly
from ui import apply_shadcn_theme, metric_cards, page_header, section_heading


st.set_page_config(page_title="Monthly Top Complaints", layout="wide")
apply_shadcn_theme()
page_header(
    title="Monthly Top Complaints",
    description="Monthly complaint rankings by borough.",
    source=f"{get_configured_base_url()}/api/v1/requests/top-complaints-monthly",
)

start_date = st.date_input("Start Month", value=None, key="top-start")
end_date = st.date_input("End Month", value=None, key="top-end")
borough = st.text_input("Borough (optional)", value="", key="top-borough")


@st.cache_data(ttl=300)
def load_data(start_date_value: str | None, end_date_value: str | None, borough_value: str) -> pd.DataFrame:
    data = get_top_complaints_monthly(
        start_date=start_date_value,
        end_date=end_date_value,
        borough=borough_value or None,
    )
    return pd.DataFrame(data) if data else pd.DataFrame()


try:
    df = load_data(
        start_date.isoformat() if start_date else None,
        end_date.isoformat() if end_date else None,
        borough,
    )
except ApiClientError as exc:
    st.error(str(exc))
    st.stop()

if df.empty:
    st.warning("No monthly ranking records returned by the API.")
    st.stop()

df["month"] = pd.to_datetime(df["month"], errors="coerce")
df = df.sort_values(["month", "borough", "rank_in_borough"])

metric_cards(
    [
        {"title": "Rows", "value": len(df), "description": "records returned"},
        {"title": "Boroughs", "value": df["borough"].nunique(), "description": "boroughs represented"},
        {"title": "Complaint Types", "value": df["complaint_type"].nunique(), "description": "unique complaint types"},
    ],
    key_prefix="top-complaints-metrics",
)

section_heading("Top Rank Trend")
top_rank = df[df["rank_in_borough"] == 1].groupby("month")["request_count"].sum()
st.line_chart(top_rank, use_container_width=True)

section_heading("Data")
st.dataframe(df, use_container_width=True, height=450)

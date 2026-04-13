from pathlib import Path
import sys

import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))

from api_client import ApiClientError, get_configured_base_url, get_location_hotspots
from ui import apply_shadcn_theme, metric_cards, page_header, section_heading


st.set_page_config(page_title="Location Hotspots", layout="wide")
apply_shadcn_theme()
page_header(
    title="Location Hotspots",
    description="Hotspot concentrations by borough, zip, and complaint type.",
    source=f"{get_configured_base_url()}/api/v1/requests/location-hotspots",
)

borough = st.text_input("Borough (optional)", value="", key="hotspots-borough")
complaint_type = st.text_input("Complaint Type (optional)", value="", key="hotspots-complaint")


@st.cache_data(ttl=300)
def load_data(borough_value: str, complaint_value: str) -> pd.DataFrame:
    data = get_location_hotspots(
        borough=borough_value or None,
        complaint_type=complaint_value or None,
    )
    return pd.DataFrame(data) if data else pd.DataFrame()


try:
    df = load_data(borough, complaint_type)
except ApiClientError as exc:
    st.error(str(exc))
    st.stop()

if df.empty:
    st.warning("No hotspot records returned by the API.")
    st.stop()

metric_cards(
    [
        {"title": "Rows", "value": len(df), "description": "hotspot groups returned"},
        {"title": "Total Requests", "value": int(pd.to_numeric(df["request_count"], errors="coerce").sum()),
         "description": "sum of grouped counts"},
        {"title": "Unique Zips", "value": df["incident_zip"].nunique(), "description": "zip hotspots"},
    ],
    key_prefix="hotspot-metrics",
)

section_heading("Top Hotspots")
top_hotspots = df.sort_values("request_count", ascending=False).head(20)
st.bar_chart(top_hotspots.set_index("incident_zip")["request_count"], use_container_width=True)

section_heading("Data")
st.dataframe(df, use_container_width=True, height=450)

import streamlit as st
import pandas as pd

from api_client import (
    ApiClientError,
    get_configured_base_url,
    get_requests,
    get_requests_by_complaint_type,
    get_requests_daily,
)
from ui import apply_shadcn_theme, dashboard_card, metric_cards, page_header, section_heading


st.set_page_config(page_title="NYC 311 Dashboard", layout="wide")
apply_shadcn_theme()

page_header(
    title="NYC 311 API Dashboard",
    description="Endpoint summaries with live metrics for NYC 311 request data.",
    source=get_configured_base_url(),
)

st.info(
    f"API base URL: `{get_configured_base_url()}`\n\n"
    "Use the sidebar to switch between pages."
)

@st.cache_data(ttl=300)
def load_requests_data() -> pd.DataFrame:
    data = get_requests()
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


@st.cache_data(ttl=300)
def load_daily_data() -> pd.DataFrame:
    data = get_requests_daily()
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


@st.cache_data(ttl=300)
def load_complaint_type_data() -> pd.DataFrame:
    data = get_requests_by_complaint_type()
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


def render_raw_requests_summary() -> None:
    dashboard_card(
        title="Raw Requests",
        content="Filterable raw request records and request-level status data.",
        description=f"{get_configured_base_url()}/api/v1/requests/",
        key="raw-requests-card",
    )
    try:
        df = load_requests_data()
    except ApiClientError as exc:
        st.error(str(exc))
        return

    if df.empty:
        st.warning("No records returned.")
        return

    metrics = [
        {"title": "Total Rows", "value": len(df), "description": "rows currently returned"},
    ]
    if "is_closed" in df.columns:
        closed_count = int(df["is_closed"].fillna(False).sum())
        metrics.extend(
            [
                {"title": "Closed Requests", "value": closed_count, "description": "records marked closed"},
                {"title": "Open Requests", "value": len(df) - closed_count, "description": "records still open"},
            ]
        )
    metric_cards(metrics, key_prefix="home-raw-metrics")


def render_daily_trends_summary() -> None:
    dashboard_card(
        title="Daily Trends",
        content="Daily totals and closure performance over time.",
        description=f"{get_configured_base_url()}/api/v1/requests/daily",
        key="daily-trends-card",
    )
    try:
        df = load_daily_data()
    except ApiClientError as exc:
        st.error(str(exc))
        return

    if df.empty:
        st.warning("No records returned.")
        return

    metrics = []
    if "total_requests" in df.columns:
        latest_total = pd.to_numeric(df["total_requests"], errors="coerce").dropna()
        if not latest_total.empty:
            metrics.append(
                {"title": "Latest Total Requests", "value": int(latest_total.iloc[-1]), "description": "most recent daily total"}
            )
    if "pct_closed" in df.columns:
        latest_close_rate = pd.to_numeric(df["pct_closed"], errors="coerce").dropna()
        if not latest_close_rate.empty:
            metrics.append(
                {"title": "Latest Close Rate", "value": f"{float(latest_close_rate.iloc[-1]) * 100:.1f}%", "description": "share of closed requests"}
            )
    metric_cards(metrics, key_prefix="home-daily-metrics")


def render_complaint_type_summary() -> None:
    dashboard_card(
        title="Complaint Type Analysis",
        content="Top complaint categories with totals and resolution indicators.",
        description=f"{get_configured_base_url()}/api/v1/requests/by-complaint-type",
        key="complaint-type-card",
    )
    try:
        df = load_complaint_type_data()
    except ApiClientError as exc:
        st.error(str(exc))
        return

    if df.empty:
        st.warning("No records returned.")
        return

    metrics = [{"title": "Complaint Types", "value": len(df), "description": "unique rows in current response"}]
    if "total_requests" in df.columns:
        total_requests = pd.to_numeric(df["total_requests"], errors="coerce").sum()
        metrics.append(
            {"title": "Total Requests", "value": int(total_requests), "description": "sum across complaint types"}
        )
    metric_cards(metrics, key_prefix="home-complaint-metrics")

section_heading("Endpoint Summaries", "Use the page navigation to explore details.")
card_cols = st.columns(3)
with card_cols[0]:
    render_raw_requests_summary()
with card_cols[1]:
    render_daily_trends_summary()
with card_cols[2]:
    render_complaint_type_summary()

section_heading("Pages")
page_cols = st.columns(3)
with page_cols[0]:
    dashboard_card(
        title="Raw Requests",
        content="Filterable table and top-level metrics",
        description="/api/v1/requests/",
        key="page-raw",
    )
with page_cols[1]:
    dashboard_card(
        title="Daily Trends",
        content="Request totals and closure metrics",
        description="/api/v1/requests/daily",
        key="page-daily",
    )
with page_cols[2]:
    dashboard_card(
        title="Complaint Type Analysis",
        content="Top complaint categories and resolution indicators",
        description="/api/v1/requests/by-complaint-type",
        key="page-complaint",
    )

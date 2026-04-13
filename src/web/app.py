import streamlit as st
import pandas as pd

from api_client import (
    ApiClientError,
    get_configured_base_url,
    get_requests,
    get_requests_by_agency_daily,
    get_requests_by_complaint_type,
    get_requests_daily,
    get_requests_geo_daily,
    get_open_backlog_daily,
    get_sla_performance_daily,
    get_top_complaints_monthly,
    get_resolution_time_distribution,
    get_location_hotspots,
    get_request_fact,
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


@st.cache_data(ttl=300)
def load_agency_daily_data() -> pd.DataFrame:
    data = get_requests_by_agency_daily()
    return pd.DataFrame(data) if data else pd.DataFrame()


@st.cache_data(ttl=300)
def load_geo_daily_data() -> pd.DataFrame:
    data = get_requests_geo_daily()
    return pd.DataFrame(data) if data else pd.DataFrame()


@st.cache_data(ttl=300)
def load_backlog_daily_data() -> pd.DataFrame:
    data = get_open_backlog_daily()
    return pd.DataFrame(data) if data else pd.DataFrame()


@st.cache_data(ttl=300)
def load_sla_daily_data() -> pd.DataFrame:
    data = get_sla_performance_daily()
    return pd.DataFrame(data) if data else pd.DataFrame()


@st.cache_data(ttl=300)
def load_top_complaints_monthly_data() -> pd.DataFrame:
    data = get_top_complaints_monthly()
    return pd.DataFrame(data) if data else pd.DataFrame()


@st.cache_data(ttl=300)
def load_resolution_distribution_data() -> pd.DataFrame:
    data = get_resolution_time_distribution()
    return pd.DataFrame(data) if data else pd.DataFrame()


@st.cache_data(ttl=300)
def load_location_hotspots_data() -> pd.DataFrame:
    data = get_location_hotspots()
    return pd.DataFrame(data) if data else pd.DataFrame()


@st.cache_data(ttl=300)
def load_request_fact_data() -> pd.DataFrame:
    data = get_request_fact()
    return pd.DataFrame(data) if data else pd.DataFrame()


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

section_heading("New Gold Endpoints")
gold_cols_1 = st.columns(4)
with gold_cols_1[0]:
    dashboard_card(
        title="Agency Performance",
        content=f"{len(load_agency_daily_data())} rows",
        description="/api/v1/requests/by-agency-daily",
        key="gold-agency",
    )
with gold_cols_1[1]:
    dashboard_card(
        title="Geo Daily",
        content=f"{len(load_geo_daily_data())} rows",
        description="/api/v1/requests/geo-daily",
        key="gold-geo",
    )
with gold_cols_1[2]:
    dashboard_card(
        title="Open Backlog",
        content=f"{len(load_backlog_daily_data())} rows",
        description="/api/v1/requests/open-backlog-daily",
        key="gold-backlog",
    )
with gold_cols_1[3]:
    dashboard_card(
        title="SLA Performance",
        content=f"{len(load_sla_daily_data())} rows",
        description="/api/v1/requests/sla-performance-daily",
        key="gold-sla",
    )

gold_cols_2 = st.columns(4)
with gold_cols_2[0]:
    dashboard_card(
        title="Top Complaints Monthly",
        content=f"{len(load_top_complaints_monthly_data())} rows",
        description="/api/v1/requests/top-complaints-monthly",
        key="gold-top-complaints",
    )
with gold_cols_2[1]:
    dashboard_card(
        title="Resolution Distribution",
        content=f"{len(load_resolution_distribution_data())} rows",
        description="/api/v1/requests/resolution-time-distribution",
        key="gold-resolution-dist",
    )
with gold_cols_2[2]:
    dashboard_card(
        title="Location Hotspots",
        content=f"{len(load_location_hotspots_data())} rows",
        description="/api/v1/requests/location-hotspots",
        key="gold-hotspots",
    )
with gold_cols_2[3]:
    dashboard_card(
        title="Request Fact",
        content=f"{len(load_request_fact_data())} rows",
        description="/api/v1/requests/request-fact",
        key="gold-request-fact",
    )

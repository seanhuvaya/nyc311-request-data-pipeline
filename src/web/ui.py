from __future__ import annotations

from typing import Iterable

import streamlit as st
import streamlit_shadcn_ui as ui


def apply_shadcn_theme() -> None:
    """Inject small CSS tweaks for a cleaner shadcn-like baseline."""
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }
        .stCaption {
            color: rgba(100, 116, 139, 1);
        }
        .stDataFrame {
            border: 1px solid rgba(226, 232, 240, 0.9);
            border-radius: 12px;
        }
        [data-testid="stSidebar"] {
            border-right: 1px solid rgba(226, 232, 240, 0.9);
        }
        .dashboard-card {
            border: 1px solid rgba(226, 232, 240, 0.9);
            border-radius: 12px;
            padding: 1rem;
            min-height: 176px;
            height: 176px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .dashboard-card-title {
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        .dashboard-card-content {
            line-height: 1.4;
            margin-bottom: 0.75rem;
        }
        .dashboard-card-description {
            color: rgba(100, 116, 139, 1);
            font-size: 0.82rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, description: str, source: str | None = None) -> None:
    st.title(title)
    st.caption(description)
    if source:
        ui.badges(
            badge_list=[
                ("source", "secondary"),
                (source, "outline"),
            ],
            key=f"badge-{title}",
        )


def metric_cards(metrics: Iterable[dict], key_prefix: str) -> None:
    metric_list = list(metrics)
    if not metric_list:
        return

    cols = st.columns(len(metric_list))
    for idx, metric in enumerate(metric_list):
        with cols[idx]:
            ui.metric_card(
                title=str(metric.get("title", "")),
                content=str(metric.get("value", "N/A")),
                description=str(metric.get("description", "")),
                key=f"{key_prefix}-{idx}",
            )


def section_heading(title: str, caption: str | None = None) -> None:
    st.subheader(title)
    if caption:
        st.caption(caption)


def dashboard_card(title: str, content: str, description: str, key: str) -> None:
    st.markdown(
        f"""
        <div class="dashboard-card" id="{key}">
            <div>
                <div class="dashboard-card-title">{title}</div>
                <div class="dashboard-card-content">{content}</div>
            </div>
            <div class="dashboard-card-description">{description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


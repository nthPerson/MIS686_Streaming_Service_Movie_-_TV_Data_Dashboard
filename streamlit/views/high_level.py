"""High-level analytics view with shared sidebar filters."""

from __future__ import annotations

import logging

import streamlit as st

from access import require_user
from config import get_settings
from filters import FilterState, render_sidebar_filters
import queries
from views import catalog, distribution, overview, recommendations, trends

logger = logging.getLogger(__name__)


@st.cache_data(show_spinner=False)
def _load_filter_options():
    return queries.fetch_filter_options()


def _render_sidebar(settings_summary: str) -> FilterState | None:
    st.sidebar.title("Filters")
    st.sidebar.caption(settings_summary)
    try:
        filter_options = _load_filter_options()
    except Exception as exc:  # pragma: no cover - bubbled to UI
        st.sidebar.error("Unable to load filter metadata.")
        raise

    return render_sidebar_filters(filter_options)


def render() -> None:
    user = require_user()
    settings = get_settings()

    try:
        filters = _render_sidebar(settings.settings_summary())
    except Exception as exc:  # pragma: no cover - surfaced to UI
        logger.exception("Failed to initialize sidebar filters")
        st.error("Failed to initialize sidebar filters.")
        st.exception(exc)
        return

    st.title("High-Level Analytics")
    st.caption("Original dashboard components retained with sidebar-filtered data.")

    status_col, _ = st.columns([3, 1])
    with status_col:
        st.success(f"Logged in as {user.username} ({user.role}).")

    overview.render(filters)
    distribution.render(filters)
    trends.render(filters)
    recommendations.render(filters)
    catalog.render(filters)

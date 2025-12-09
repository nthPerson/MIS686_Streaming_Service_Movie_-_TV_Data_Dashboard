"""High-level analytics view with shared sidebar filters."""

from __future__ import annotations

import logging

import streamlit as st
import plotly.express as px

from access import require_user
from config import get_settings
from filters import FilterState, render_sidebar_filters
import queries
from views import catalog, distribution, overview, recommendations, trends

logger = logging.getLogger(__name__)


@st.cache_data(show_spinner=False)
def _load_filter_options():
    return queries.fetch_filter_options()


def _render_sidebar() -> FilterState | None:
    st.sidebar.title("Filters")
    try:
        filter_options = _load_filter_options()
    except Exception as exc:  # pragma: no cover - bubbled to UI
        st.sidebar.error("Unable to load filter metadata.")
        raise

    return render_sidebar_filters(filter_options)


def _render_stored_procedure_preview(filters: FilterState | None) -> None:
    st.subheader("Stored Procedure Preview")

    proc_df = queries.fetch_titles_via_stored_procedure(filters)
    if proc_df.empty:
        st.info("Stored procedure returned no rows for the selected filters.")
        return

    summary = (
        proc_df.groupby(["service_name", "content_type"], as_index=False)["title_id"]
        .count()
        .rename(columns={"title_id": "title_count"})
        .sort_values(["title_count", "service_name"], ascending=[False, True])
    )

    fig = px.bar(
        summary,
        x="service_name",
        y="title_count",
        color="content_type",
        barmode="stack",
        labels={"service_name": "Platform", "title_count": "Titles", "content_type": "Type"},
        title="Titles by platform returned from sp_get_titles_for_dashboard",
    )
    st.plotly_chart(fig, use_container_width=True)

    table = proc_df.rename(
        columns={
            "service_name": "Platform",
            "global_title_name": "Title",
            "content_type": "Type",
            "release_year": "Release Year",
            "runtime_minutes": "Runtime (min)",
            "num_seasons": "Seasons",
        }
    ).sort_values(["Platform", "Release Year", "Title"])

    st.dataframe(
        table[["Platform", "Title", "Type", "Release Year", "Runtime (min)", "Seasons"]].head(50),
        use_container_width=True,
    )

    st.caption(
        "Powered by sp_get_titles_for_dashboard (service filter applies when a single platform is selected; type and release year always apply)."
    )


def render() -> None:
    user = require_user()
    # Ensure settings are loaded without surfacing connection details in the UI sidebar
    get_settings()

    try:
        filters = _render_sidebar()
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

    _render_stored_procedure_preview(filters)
    st.divider()

    overview.render(filters)
    distribution.render(filters)
    trends.render(filters)
    recommendations.render(filters)
    catalog.render(filters)

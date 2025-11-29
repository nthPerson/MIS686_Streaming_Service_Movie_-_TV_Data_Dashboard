"""Streamlit entry point orchestrating sidebar filters and view sections."""

from __future__ import annotations

import streamlit as st

# from .config import get_settings
# from .filters import FilterState, render_sidebar_filters
# from . import queries
# from .views import catalog, distribution, overview, recommendations, trends

from config import get_settings
from filters import FilterState, render_sidebar_filters
import queries
from views import catalog, distribution, overview, recommendations, trends


@st.cache_data(show_spinner=False)
def _load_filter_options():
    return queries.fetch_filter_options()


def _render_sidebar(settings_summary: str) -> FilterState | None:
    st.sidebar.title("Filters")
    st.sidebar.caption(settings_summary)
    try:
        filter_options = _load_filter_options()
    except Exception as exc:  # pragma: no cover - surfaced to UI instead
        st.sidebar.error(f"Unable to load filter metadata: {exc}")
        raise

    return render_sidebar_filters(filter_options)


def run() -> None:
    st.set_page_config(page_title="Streaming Market Intelligence", layout="wide")
    settings = get_settings()
    filters: FilterState | None

    try:
        filters = _render_sidebar(settings.settings_summary())
    except Exception:
        st.stop()
        return

    st.title("Streaming Media Intelligence Dashboard")
    st.caption("Explore catalog availability, content mix, and platform expansion trends.")

    overview.render(filters)
    distribution.render(filters)
    trends.render(filters)
    recommendations.render(filters)
    catalog.render(filters)


if __name__ == "__main__":
    run()

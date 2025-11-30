"""Streamlit entry point orchestrating sidebar filters and view sections."""

from __future__ import annotations

import logging

import streamlit as st

# from .config import get_settings
# from .filters import FilterState, render_sidebar_filters
# from . import queries
# from .views import catalog, distribution, overview, recommendations, trends

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
    except Exception as exc:  # pragma: no cover - surfaced to UI instead
        st.sidebar.error(f"Unable to load filter metadata: {exc}")
        raise

    return render_sidebar_filters(filter_options)


def run() -> None:
    st.set_page_config(page_title="Streaming Market Intelligence", layout="wide")
    user = require_user()
    settings = get_settings()
    filters: FilterState | None

    try:
        filters = _render_sidebar(settings.settings_summary())
    except Exception as exc:
        logger.exception("Failed to initialize sidebar filters")  # prints full stack trace
        st.error("Failed to initialize sidebar filters.")
        st.exception(exc)
        return

    st.title("Streaming Media Intelligence Dashboard")
    st.caption("Explore catalog availability, content mix, and platform expansion trends.")

    st.success(f"Logged in as {user.username} ({user.role}).")
    logout_col, links_col = st.columns([1, 3])
    with logout_col:
        if st.button("Log out", type="secondary"):
            st.session_state.pop("current_user", None)
            if hasattr(st, "switch_page"):
                st.switch_page("pages/01_Login_Signup.py")
            else:
                st.rerun()

    with links_col:
        if hasattr(st, "page_link"):
            st.page_link("pages/01_Login_Signup.py", label="Account portal", icon="🔐")
            if user.role in ("viewer", "admin"):
                st.page_link("pages/02_Viewer_Platform.py", label="Viewer Platform Comparison", icon="📊")
            if user.role in ("analyst", "admin"):
                st.page_link("pages/03_Analyst_Advanced.py", label="Analyst Advanced Analytics", icon="🧮")
            if user.role == "admin":
                st.page_link("pages/04_Admin_Control.py", label="Admin Control Center", icon="🛠️")

    overview.render(filters)
    distribution.render(filters)
    trends.render(filters)
    recommendations.render(filters)
    catalog.render(filters)


if __name__ == "__main__":
    run()

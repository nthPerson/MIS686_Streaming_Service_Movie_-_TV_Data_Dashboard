"""Streamlit entry point orchestrating question-centric landing experience."""

from __future__ import annotations

import logging

import streamlit as st

from config import get_settings
from views import admin_dashboard, analyst_dashboard, auth_page, high_level, overview, questions, viewer_dashboard
from pathlib import Path

logger = logging.getLogger(__name__)

APP_DIR = Path(__file__).resolve().parent
LOGO_PATH = APP_DIR / "movie_monkies_logo.png"


def _render_logo() -> None:
    with st.sidebar:
        st.image(str(LOGO_PATH), width='stretch')


def _render_home_about() -> None:
    with st.sidebar:
        st.title("About this Dashboard")
        st.write(
            "To discover analytical insights related to movies and TV shows offered by Amazon Prime Video, Netlix, Hulu, and Disney+: "
            "\n- Browse the eight analytical questions"
            "\n- Change visualization filters for dynamic data analysis"
            "\n- Click the 'SQL Query' dropdowns to see the queries powering this dashboard"
            "\n- Click the 'Answer / Interpretation' drowpdowns for detailed responses to each analytical question"
            "\n- Browse user role-specific pages below for additional insights, analysis, or administative controls"
        )
        st.divider()


def _render_home() -> None:
    st.title("Streaming Platform Content Analytics Dashboard")
    st.markdown("###### A multi-dimensional comparison of catalog size, genre distribution, geographic diversity, and maturity profiles of four major streaming services, analyzed through eight analytical questions.")
    # st.caption("A multi-dimensional comparison of catalog size, genre distribution, geographic diversity, and maturity profiles of four major streaming services, analyzed through eight analytical questions.")
    overview.render(None)
    st.divider()
    questions.render_all()


NAV_PAGES = {
    "home": {"label": "Analytical Questions", "icon": "🏠", "roles": None, "render": _render_home},
    "high_level": {"label": "High-Level Analytics", "icon": "📊", "roles": None, "render": high_level.render},
    "viewer": {"label": "Platform Comparison (Viewer)", "icon": "🎯", "roles": ["viewer"], "render": viewer_dashboard.render},
    "analyst": {"label": "Advanced Analytics (Analyst)", "icon": "🧮", "roles": ["analyst"], "render": analyst_dashboard.render},
    "admin": {"label": "Control Center (Admin)", "icon": "🛠️", "roles": ["admin"], "render": admin_dashboard.render},
}


def _render_sidebar_navigation(user_role: str) -> str:
    st.sidebar.header("Navigate")

    allowed_keys: list[str] = []
    labels: list[str] = []
    for key, meta in NAV_PAGES.items():
        allowed_roles = meta.get("roles")
        if user_role == "admin" or allowed_roles is None or user_role in allowed_roles:
            allowed_keys.append(key)
            labels.append(f"{meta['icon']}  {meta['label']}")

    current_key = st.session_state.get("current_page", allowed_keys[0])
    default_index = allowed_keys.index(current_key) if current_key in allowed_keys else 0

    chosen_label = st.sidebar.radio(
        "Navigate",
        labels,
        index=default_index,
        label_visibility="collapsed",
    )

    chosen_key = allowed_keys[labels.index(chosen_label)]
    st.session_state["current_page"] = chosen_key
    st.sidebar.caption(f"Current role: **{user_role}**")
    return chosen_key


def _render_user_status(user) -> None:
    status_col, action_col = st.columns([3, 1])
    with status_col:
        st.success(f"Logged in as {user.username} ({user.role}).")
    with action_col:
        if st.button("Log out", type="secondary"):
            st.session_state.pop("current_user", None)
            st.session_state["current_page"] = "access"
            st.rerun()


def _maybe_reroute(current_key: str, chosen_key: str) -> None:
    """If navigation selection changes, update state and rerun immediately."""
    if chosen_key != current_key:
        st.session_state["current_page"] = chosen_key
        st.rerun()


def run() -> None:
    st.set_page_config(page_title="Streaming Market Intelligence", layout="wide")
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "home"

    user = st.session_state.get("current_user")
    if not user:
        st.session_state["current_page"] = "access"
        # _render_about_sidebar()
        auth_page.render()
        return

    get_settings()
    active_page = st.session_state.get("current_page", "home")

    if active_page == "home":
        _render_logo()
        _render_home_about()
        chosen = _render_sidebar_navigation(user.role)
        _maybe_reroute(active_page, chosen)
        _render_user_status(user)
        _render_home()
    elif active_page == "high_level":
        _render_logo()
        _render_user_status(user)
        high_level.render()
        # st.sidebar.divider()
        chosen = _render_sidebar_navigation(user.role)
        _maybe_reroute(active_page, chosen)
    elif active_page == "viewer":
        _render_logo()
        with st.sidebar:
            st.info("No filters required for this page. Use the navigation below to explore other views.")
            st.divider()
        chosen = _render_sidebar_navigation(user.role)
        _maybe_reroute(active_page, chosen)
        _render_user_status(user)
        viewer_dashboard.render()
    elif active_page == "analyst":
        _render_logo()
        with st.sidebar:
            st.subheader("Filters")
            st.write("Filters are configured within this page's controls.")
            st.divider()
        chosen = _render_sidebar_navigation(user.role)
        _maybe_reroute(active_page, chosen)
        _render_user_status(user)
        analyst_dashboard.render()
    elif active_page == "admin":
        _render_logo()
        with st.sidebar:
            st.info("No filters required for this page. Use the navigation below to explore other views.")
            st.divider()
        chosen = _render_sidebar_navigation(user.role)
        _maybe_reroute(active_page, chosen)
        _render_user_status(user)
        admin_dashboard.render()
    else:
        st.session_state["current_page"] = "home"
        st.rerun()


if __name__ == "__main__":
    run()

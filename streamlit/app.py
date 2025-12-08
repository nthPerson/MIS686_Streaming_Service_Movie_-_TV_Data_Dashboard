"""Streamlit entry point orchestrating question-centric landing experience."""

from __future__ import annotations

import logging

import streamlit as st

from config import get_settings
from views import admin_dashboard, analyst_dashboard, auth_page, high_level, overview, questions, viewer_dashboard

logger = logging.getLogger(__name__)


def _render_about_sidebar() -> None:
    st.sidebar.title("About this Dashboard")
    st.sidebar.write(
        "A multi-dimensional comparison of catalog size, genre distribution, geographic diversity, and maturity profiles of four major streaming services, analyzed through eight analytical questions."
    )
    st.sidebar.divider()


def _render_home() -> None:
    st.title("Streaming Platform Content Analytics Dashboard")
    st.caption("Landing hub for the course's eight analytical questions.")
    overview.render(None)
    st.divider()
    questions.render_all()


NAV_PAGES = {
    "home": {"label": "Analytical Questions", "icon": "🏠", "roles": None, "render": _render_home},
    "high_level": {"label": "High-Level Analytics", "icon": "📊", "roles": None, "render": high_level.render},
    "viewer": {"label": "Viewer Platform Comparison", "icon": "🎯", "roles": ["viewer"], "render": viewer_dashboard.render},
    "analyst": {"label": "Analyst Advanced Analytics", "icon": "🧮", "roles": ["analyst"], "render": analyst_dashboard.render},
    "admin": {"label": "Admin Control Center", "icon": "🛠️", "roles": ["admin"], "render": admin_dashboard.render},
}


def _render_sidebar_navigation(user_role: str) -> str:
    _render_about_sidebar()
    st.sidebar.subheader("Navigate")

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


def run() -> None:
    st.set_page_config(page_title="Streaming Market Intelligence", layout="wide")
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "home"

    user = st.session_state.get("current_user")
    if not user:
        st.session_state["current_page"] = "access"
        _render_about_sidebar()
        auth_page.render()
        return

    get_settings()
    active_page = _render_sidebar_navigation(user.role)
    _render_user_status(user)

    if active_page == "home":
        _render_home()
    else:
        NAV_PAGES[active_page]["render"]()


if __name__ == "__main__":
    run()

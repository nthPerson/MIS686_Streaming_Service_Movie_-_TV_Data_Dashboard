"""Streamlit entry point orchestrating question-centric landing experience."""

from __future__ import annotations

import logging

import streamlit as st

from access import require_user
from config import get_settings
from views import overview, questions

logger = logging.getLogger(__name__)


def _render_sidebar_navigation(user_role: str) -> None:
    st.sidebar.title("About this Dashboard")
    st.sidebar.write(
        "Answer eight course-driven analytical questions covering platform scale, "
        "geographies, genres, and maturity ratings."
    )
    st.sidebar.divider()
    st.sidebar.subheader("Navigate")
    if hasattr(st.sidebar, "page_link"):
        links = [
            {"page": "app.py", "label": "Analytical Questions", "icon": "🏠", "roles": None},
            {
                "page": "pages/05_High_Level_Analytics.py",
                "label": "High-Level Analytics",
                "icon": "📊",
                "roles": None,
            },
            {
                "page": "pages/02_Viewer_Platform.py",
                "label": "Viewer Platform Comparison",
                "icon": "🎯",
                "roles": ["viewer"],
            },
            {
                "page": "pages/03_Analyst_Advanced.py",
                "label": "Analyst Advanced Analytics",
                "icon": "🧮",
                "roles": ["analyst"],
            },
            {
                "page": "pages/04_Admin_Control.py",
                "label": "Admin Control Center",
                "icon": "🛠️",
                "roles": ["admin"],
            },
        ]

        for link in links:
            allowed_roles = link.get("roles")
            if user_role == "admin" or allowed_roles is None or user_role in allowed_roles:
                st.sidebar.page_link(link["page"], label=link["label"], icon=link["icon"])
    st.sidebar.caption(f"Current role: **{user_role}**")


def run() -> None:
    st.set_page_config(page_title="Streaming Market Intelligence", layout="wide")
    user = require_user()
    get_settings()
    _render_sidebar_navigation(user.role)

    st.title("Streaming Media Intelligence Dashboard")
    st.caption("Landing hub for the course's eight analytical questions.")

    status_col, action_col = st.columns([3, 1])
    with status_col:
        st.success(f"Logged in as {user.username} ({user.role}).")
    with action_col:
        if st.button("Log out", type="secondary"):
            st.session_state.pop("current_user", None)
            if hasattr(st, "switch_page"):
                st.switch_page("pages/01_Login_Signup.py")
            else:
                st.rerun()

    overview.render(None)
    st.divider()
    questions.render_all()


if __name__ == "__main__":
    run()

"""Helpers for enforcing authentication and role-based access."""

from __future__ import annotations

from typing import Iterable

import streamlit as st

from auth import AuthenticatedUser


def _redirect_to_login() -> None:
    st.session_state["current_page"] = "access"
    st.rerun()


def require_user(allowed_roles: Iterable[str] | None = None) -> AuthenticatedUser:
    """Ensure a user is logged in (and optionally authorized) before proceeding."""

    user = st.session_state.get("current_user")
    if not user:
        _redirect_to_login()

    if allowed_roles and user.role not in allowed_roles:
        if user.role == "admin":  # admins can see everything
            return user
        st.error("You do not have permission to view this page.")
        st.stop()

    return user

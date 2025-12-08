"""Account access view with login and signup flows."""

from __future__ import annotations

import streamlit as st
from pathlib import Path

from auth import authenticate_user, list_roles, register_user


def render() -> None:
    col1, col2 = st.columns(2)

    with col1:
        st.header("Welcome to our login page!", divider="gray")

    with col2:
        # st.header("Welcome to our login page!", divider="gray")
        APP_DIR = Path(__file__).resolve().parent.parent  # Get the parent directory of this file
        LOGO_PATH = APP_DIR / "movie_monkies_logo.png"
        st.image(str(LOGO_PATH), width=150)  

    st.markdown("### Please log in or create an account below:")
    st.caption("Create an account using the 'Sign Up' tab or log in with existing credentials on the 'Log In' tab.")

    login_tab, signup_tab = st.tabs(["Log In", "Sign Up"])

    with login_tab:
        with st.form("login_form", clear_on_submit=False):
            login_username = st.text_input("Username", key="login_username")
            login_password = st.text_input("Password", type="password", key="login_password")
            login_submit = st.form_submit_button("Log In")

        if login_submit:
            if not login_username or not login_password:
                st.error("Please supply both username and password.")
            else:
                success, message, user = authenticate_user(login_username.strip(), login_password)
                if success:
                    st.session_state["current_user"] = user
                    st.session_state["current_page"] = "home"
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

    with signup_tab:
        st.write("Choose a role to unlock the corresponding role-specific pages.")
        available_roles = list_roles()
        with st.form("signup_form", clear_on_submit=True):
            signup_username = st.text_input("Username", key="signup_username")
            signup_email = st.text_input("Email", key="signup_email")
            signup_password = st.text_input("Password", type="password", key="signup_password")
            signup_role = st.selectbox("Role", available_roles, key="signup_role")
            signup_submit = st.form_submit_button("Create Account")

        if signup_submit:
            if not (signup_username and signup_email and signup_password):
                st.error("All fields are required.")
            else:
                success, message = register_user(
                    signup_username.strip(),
                    signup_email.strip(),
                    signup_password,
                    signup_role,
                )
                if success:
                    st.success(message)
                else:
                    st.error(message)

    st.divider()
    if "current_user" in st.session_state:
        user = st.session_state["current_user"]
        st.info(f"Logged in as {user.username} ({user.role}).")
        if st.button("Log out", type="secondary"):
            st.session_state.pop("current_user", None)
            st.session_state["current_page"] = "access"
            st.rerun()
    else:
        st.info("You are not logged in yet.")

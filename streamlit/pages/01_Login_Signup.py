"""Standalone page for logging in or registering toy accounts."""

from __future__ import annotations

import streamlit as st

from auth import authenticate_user, list_roles, register_user

st.set_page_config(page_title="Account Access", page_icon="🔐")

st.title("Account Access")
st.caption("Create a toy account or log in with existing credentials.")

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
                st.success(message)
                st.session_state["current_user"] = user
                if hasattr(st, "switch_page"):
                    st.switch_page("app.py")
                else:
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
        st.rerun()
    if hasattr(st, "page_link"):
        st.page_link("app.py", label="⬅️ Go to dashboard", icon="🏠")
else:
    st.info("You are not logged in yet.")

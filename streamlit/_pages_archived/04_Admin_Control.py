"""Admin-only control center for managing application users."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from access import require_user
from auth import (
    delete_user,
    fetch_user_audit,
    fetch_users,
    list_roles,
    register_user,
    toggle_user_active,
    update_user_role,
)

st.set_page_config(page_title="Admin Control Center", page_icon="🛠️")
user = require_user(["admin"])

st.title("Admin Control Center")
st.caption("Manage application users and audit activity.")

roles = list_roles()
users = fetch_users()
users_df = pd.DataFrame(users)

if users_df.empty:
    st.warning("No users found.")
else:
    st.dataframe(
        users_df.rename(
            columns={
                "role_name": "Role",
                "is_active": "Active",
                "created_at": "Created",
                "last_login_at": "Last Login",
            }
        ),
        use_container_width=True,
    )

col_add, col_role, col_status, col_delete = st.columns(4)
with col_add:
    st.subheader("Create user")
    with st.form("create_user_form", clear_on_submit=True):
        new_username = st.text_input("Username")
        new_email = st.text_input("Email")
        new_password = st.text_input("Password", type="password")
        new_role = st.selectbox("Role", roles)
        create_submit = st.form_submit_button("Create")
    if create_submit:
        if not (new_username and new_email and new_password):
            st.error("All fields required.")
        else:
            success, message = register_user(new_username.strip(), new_email.strip(), new_password, new_role)
            if success:
                st.success(message)
                # st.rerun()
                st.rerun()
            else:
                st.error(message)

with col_role:
    st.subheader("Change role")
    with st.form("change_role_form"):
        user_choices = {f"{row['username']} ({row['role_name']})": row["user_id"] for row in users}
        if user_choices:
            selected_user_label = st.selectbox("User", list(user_choices.keys()))
            new_role_name = st.selectbox("New role", roles, key="role_change")
            role_submit = st.form_submit_button("Update")
        else:
            selected_user_label = None
            role_submit = False
    if role_submit and selected_user_label:
        success, message = update_user_role(user_choices[selected_user_label], new_role_name)
        if success:
            st.success(message)
            st.rerun()
        else:
            st.error(message)

with col_status:
    st.subheader("Toggle active")
    with st.form("toggle_active_form"):
        status_choices = {f"{row['username']} ({'active' if row['is_active'] else 'inactive'})": (row["user_id"], not row["is_active"]) for row in users}
        if status_choices:
            status_label = st.selectbox("User", list(status_choices.keys()))
            toggle_submit = st.form_submit_button("Toggle")
        else:
            status_label = None
            toggle_submit = False
    if toggle_submit and status_label:
        user_id, new_status = status_choices[status_label]
        success, message = toggle_user_active(user_id, new_status)
        if success:
            st.success(message)
            st.rerun()
        else:
            st.error(message)

with col_delete:
    st.subheader("Delete user")
    with st.form("delete_user_form"):
        delete_choices = {row["username"]: row["user_id"] for row in users if row["user_id"] != user.user_id}
        if delete_choices:
            delete_label = st.selectbox("User", list(delete_choices.keys()))
            delete_submit = st.form_submit_button("Delete", type="primary")
        else:
            delete_label = None
            delete_submit = False
    if delete_submit and delete_label:
        success, message = delete_user(delete_choices[delete_label])
        if success:
            st.success(message)
            st.rerun()
        else:
            st.error(message)

st.subheader("User audit log")
audits = fetch_user_audit()
audits_df = pd.DataFrame(audits)
if audits_df.empty:
    st.info("No audit records found.")
else:
    st.dataframe(audits_df, use_container_width=True)

st.success(f"Admin privileges verified for {user.username}.")
if hasattr(st, "page_link"):
    st.page_link("app.py", label="⬅️ Back to main dashboard", icon="🏠")

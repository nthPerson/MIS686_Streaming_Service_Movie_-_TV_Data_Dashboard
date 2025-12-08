"""Viewer-exclusive platform comparison dashboard."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from access import require_user
import queries

st.set_page_config(page_title="Viewer Platform Dashboard", page_icon="📊")
user = require_user(["viewer"])

st.title("Platform Comparison Dashboard")
st.caption("Aggregated from vw_service_content_summary and tailored for viewers.")

summary_df = queries.fetch_service_content_summary_view()
if summary_df.empty:
    st.warning("No platform data available.")
    st.stop()

pivot_df = (
    summary_df.pivot_table(
        index="service_name",
        columns="content_type",
        values="title_count",
        aggfunc="sum",
        fill_value=0,
    )
    .reset_index()
)

melted = pivot_df.melt(
    id_vars="service_name",
    var_name="Content Type",
    value_name="Titles",
)

fig = px.bar(
    melted,
    x="service_name",
    y="Titles",
    color="Content Type",
    barmode="stack",
    title="Movie vs TV availability by service",
)
fig.update_layout(xaxis_title="Platform", yaxis_title="Titles")

st.plotly_chart(fig, width='stretch')

st.dataframe(pivot_df.rename(columns={"service_name": "Platform"}), width='stretch')

st.success(f"You are viewing the viewer workspace, {user.username}.")
if hasattr(st, "page_link"):
    st.page_link("app.py", label="⬅️ Back to main dashboard", icon="🏠")

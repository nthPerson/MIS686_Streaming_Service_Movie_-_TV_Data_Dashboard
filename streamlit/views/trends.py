"""Temporal trend visuals driven by Plotly."""

from __future__ import annotations

import streamlit as st
import plotly.express as px

from filters import FilterState
import queries


def render(filters: FilterState | None) -> None:
    st.subheader("Release Year Momentum")
    release_df = queries.fetch_release_year_trend(filters)
    if release_df.empty:
        st.info("No release year data for the selected filters.")
    else:
        fig_release = px.line(
            release_df,
            x="release_year",
            y="title_count",
            color="service_name",
            markers=True,
            labels={"release_year": "Release Year", "title_count": "Titles", "service_name": "Platform"},
            title="Catalog growth by original release year",
        )
        st.plotly_chart(fig_release, width='stretch')

    st.divider()

    st.subheader("When Titles Hit Platforms")
    added_df = queries.fetch_date_added_trend(filters)
    if added_df.empty:
        st.info("No ingestion timing data available.")
        return

    fig_added = px.line(
        added_df,
        x="month_bucket",
        y="title_count",
        color="service_name",
        markers=False,
        labels={"month_bucket": "Month", "title_count": "Titles", "service_name": "Platform"},
        title="Monthly additions by platform",
    )
    st.plotly_chart(fig_added, width='stretch')

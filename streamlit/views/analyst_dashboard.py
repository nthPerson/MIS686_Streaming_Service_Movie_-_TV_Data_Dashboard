"""Analyst-exclusive advanced filtering and analytics view."""

from __future__ import annotations

from datetime import date

import plotly.express as px
import streamlit as st

from access import require_user
from filters import FilterState
import queries


def render() -> None:
    user = require_user(["analyst"])

    st.title("Advanced Filtering & Analytics")
    st.caption("Granular controls for analysts exploring multi-genre and ingestion trends.")

    options = queries.fetch_filter_options()

    with st.expander("Advanced Filters", expanded=True):
        services = st.multiselect(
            "Streaming services",
            options=sorted(options.services),
            default=sorted(options.services),
        )

        genres = st.multiselect(
            "Genres (multi-select)",
            options=sorted(options.genres),
            default=sorted(options.genres)[:5],
        )

        date_min, date_max = options.date_added_bounds
        default_start = date_min or date(2015, 1, 1)
        default_end = date_max or date.today()
        date_range = st.date_input(
            "Date added range",
            value=(default_start, default_end),
        )

        release_min, release_max = options.release_year_bounds
        release_range = st.slider(
            "Release year",
            min_value=int(release_min or 1900),
            max_value=int(release_max or date.today().year),
            value=(int(release_min or 1900), int(release_max or date.today().year)),
        )

    filters = FilterState(
        services=tuple(services),
        content_types=tuple(options.content_types),
        genres=tuple(genres),
        countries=(),
        release_year_range=release_range,
        date_added_range=(date_range[0], date_range[1]) if isinstance(date_range, tuple) else (default_start, default_end),
        title_search=None,
    )

    summary_col, meta_col = st.columns(2)
    with summary_col:
        st.metric("Services Selected", len(services))
        st.metric("Genres Selected", len(genres))
    with meta_col:
        st.metric("Release Window", f"{release_range[0]} - {release_range[1]}")
        st.metric("Date Added", f"{filters.date_added_range[0]} → {filters.date_added_range[1]}")

    st.subheader("Genre saturation by platform")
    genre_df = queries.fetch_genre_distribution(filters)
    if genre_df.empty:
        st.warning("No data for the selected filters.")
    else:
        heatmap_df = genre_df.pivot_table(
            index="service_name",
            columns="genre_name",
            values="title_count",
            aggfunc="sum",
            fill_value=0,
        )
        fig_heatmap = px.imshow(
            heatmap_df,
            aspect="auto",
            labels=dict(x="Genre", y="Platform", color="Titles"),
            title="Genre density heatmap",
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
        st.dataframe(heatmap_df, use_container_width=True)

    st.subheader("Content additions over time")
    trend_df = queries.fetch_date_added_trend(filters)
    if trend_df.empty:
        st.info("No date-added data for this configuration.")
    else:
        fig_trend = px.line(
            trend_df,
            x="month_bucket",
            y="title_count",
            color="service_name",
            markers=False,
            labels={"month_bucket": "Month", "title_count": "Titles", "service_name": "Platform"},
            title="Monthly additions",
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    st.subheader("Recent catalog entries")
    table_df = queries.fetch_titles_table(filters, limit=100)
    st.dataframe(table_df, use_container_width=True)

    st.success(f"Analyst workspace unlocked for {user.username}.")

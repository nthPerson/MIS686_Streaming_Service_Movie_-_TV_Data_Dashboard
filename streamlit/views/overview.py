"""High-level KPIs and platform comparisons."""

from __future__ import annotations

import streamlit as st
import plotly.express as px

from filters import FilterState
import queries


def render(filters: FilterState | None) -> None:
    metrics_df = queries.fetch_overview_metrics(filters)
    if metrics_df.empty:
        st.info("No titles match the selected filters.")
        return

    st.subheader("Platform Catalog Overview")
    metrics = metrics_df.iloc[0].to_dict()
    metric_columns = st.columns(4)
    metric_columns[0].metric("Total Titles", f"{int(metrics['total_titles']):,}")
    metric_columns[1].metric("Movies", f"{int(metrics['movie_count']):,}")
    metric_columns[2].metric("TV Shows", f"{int(metrics['tv_show_count']):,}")
    metric_columns[3].metric("Genres", f"{int(metrics['distinct_genres']):,}")

    platform_df = queries.fetch_platform_breakdown(filters)
    if platform_df.empty:
        st.warning("No platform data available for the current filters.")
        return

    melted = platform_df.melt(
        id_vars="service_name",
        value_vars=["movie_count", "tv_show_count"],
        var_name="Content Type",
        value_name="Titles",
    )
    fig = px.bar(
        melted,
        x="service_name",
        y="Titles",
        color="Content Type",
        barmode="stack",
        labels={"service_name": "Platform", "Titles": "Titles"},
        title="Movie vs TV availability by platform",
    )
    st.plotly_chart(fig, use_container_width=True)

    table_df = platform_df.rename(
        columns={
            "service_name": "Platform",
            "total_titles": "Titles",
            "movie_count": "Movies",
            "tv_show_count": "TV Shows",
        }
    )
    desired_columns = ["Platform", "Titles", "Movies", "TV Shows"]
    table_df = table_df[[col for col in desired_columns if col in table_df.columns]]

    st.dataframe(
        table_df,
        use_container_width=True,
    )

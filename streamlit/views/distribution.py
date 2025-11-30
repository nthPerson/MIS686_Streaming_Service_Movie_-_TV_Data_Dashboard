"""Genre and country composition visualizations (Matplotlib)."""

from __future__ import annotations

import matplotlib.pyplot as plt
import streamlit as st

from filters import FilterState
import queries


def render(filters: FilterState | None) -> None:
    st.subheader("Top Genres Across Platforms")
    genre_df = queries.fetch_genre_distribution(filters)
    if genre_df.empty:
        st.info("No genre data for the selected filters.")
    else:
        genre_summary = (
            genre_df.groupby("genre_name", as_index=False)["title_count"].sum().sort_values("title_count", ascending=False).head(12)
        )
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.barh(genre_summary["genre_name"], genre_summary["title_count"], color="#4C78A8")
        ax.set_xlabel("Titles")
        ax.invert_yaxis()
        ax.grid(axis="x", linestyle="--", alpha=0.4)
        fig.tight_layout()
        st.pyplot(fig)

    st.divider()

    st.subheader("Production Country Spread")
    country_df = queries.fetch_country_distribution(filters)
    if country_df.empty:
        st.info("No country data for the selected filters.")
    else:
        country_summary = country_df.head(15)
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(country_summary["country_name"], country_summary["title_count"], color="#F58518")
        ax.set_ylabel("Titles")
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        fig.tight_layout()
        st.pyplot(fig)

    st.dataframe(
        country_df.rename(columns={"country_name": "Country", "title_count": "Titles"}),
        width='stretch',
    )

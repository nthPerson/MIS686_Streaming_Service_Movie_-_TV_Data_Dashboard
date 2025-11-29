"""Lightweight similarity explorer."""

from __future__ import annotations

import streamlit as st

from filters import FilterState
import queries


def render(filters: FilterState | None) -> None:
    st.subheader("Find Similar Titles")
    search_term = st.text_input("Anchor title keyword", placeholder="e.g. marvel").strip()

    if not search_term:
        st.caption("Enter a keyword to surface titles that share the most genres.")
        return

    matches = queries.fetch_similarity_candidates(filters, search_term)
    if matches.empty:
        st.warning("No similar titles found for that keyword.")
        return

    st.dataframe(
        matches.rename(
            columns={
                "title": "Title",
                "release_year": "Release Year",
                "service_name": "Platform",
                "shared_genres": "Shared Genres",
            }
        ),
        use_container_width=True,
    )

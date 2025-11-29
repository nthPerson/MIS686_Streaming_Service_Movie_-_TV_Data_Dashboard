"""Detailed catalog table."""

from __future__ import annotations

import streamlit as st

from ..filters import FilterState
from .. import queries


def render(filters: FilterState | None) -> None:
    st.subheader("Filtered Title Catalog")
    limit = st.slider("Max rows", min_value=50, max_value=500, value=250, step=50)
    table_df = queries.fetch_titles_table(filters, limit)
    if table_df.empty:
        st.info("No titles match the current filters.")
        return

    st.dataframe(table_df, use_container_width=True)

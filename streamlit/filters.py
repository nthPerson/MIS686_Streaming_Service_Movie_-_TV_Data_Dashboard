"""Sidebar filter components and supporting dataclasses."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, Sequence

import streamlit as st


@dataclass(frozen=True)
class FilterOptions:
    """Available values that users can select in the sidebar."""

    services: Sequence[str]
    content_types: Sequence[str]
    genres: Sequence[str]
    countries: Sequence[str]
    release_year_bounds: tuple[int | None, int | None]
    date_added_bounds: tuple[date | None, date | None]

    @staticmethod
    def empty() -> "FilterOptions":
        return FilterOptions(
            services=(),
            content_types=("MOVIE", "TV_SHOW"),
            genres=(),
            countries=(),
            release_year_bounds=(None, None),
            date_added_bounds=(None, None),
        )


@dataclass(frozen=True)
class FilterState:
    """Concrete selections captured from the sidebar UI."""

    services: tuple[str, ...]
    content_types: tuple[str, ...]
    genres: tuple[str, ...]
    countries: tuple[str, ...]
    release_year_range: tuple[int | None, int | None]
    date_added_range: tuple[date | None, date | None]
    title_search: str | None


def _normalize_multiselect(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(v for v in values if v)


def render_sidebar_filters(options: FilterOptions | None = None) -> FilterState:
    """Render sidebar inputs and return the resulting selections."""

    opts = options or FilterOptions.empty()
    # st.sidebar.header("Filters")

    services = st.sidebar.multiselect(
        "Streaming services",
        options=sorted(opts.services) or [
            "Netflix",
            "Amazon Prime Video",
            "Hulu",
            "Disney+",
        ],
        default=sorted(opts.services) if opts.services else None,
    )

    content_types = st.sidebar.multiselect(
        "Content types",
        options=opts.content_types,
        default=opts.content_types,
    )

    genres = st.sidebar.multiselect(
        "Genres",
        options=sorted(opts.genres),
    )

    countries = st.sidebar.multiselect(
        "Countries",
        options=sorted(opts.countries),
    )

    release_min, release_max = opts.release_year_bounds
    release_year_range = st.sidebar.slider(
        "Release year",
        min_value=int(release_min or 1900),
        max_value=int(release_max or date.today().year),
        value=(
            int(release_min or 1900),
            int(release_max or date.today().year),
        ),
    )

    date_min, date_max = opts.date_added_bounds
    date_added_range = st.sidebar.date_input(
        "Date added range",
        value=(date_min or date(2010, 1, 1), date_max or date.today()),
    )

    title_search = st.sidebar.text_input(
        "Title search",
        placeholder="e.g., Star Wars",
    )

    return FilterState(
        services=_normalize_multiselect(services),
        content_types=_normalize_multiselect(content_types),
        genres=_normalize_multiselect(genres),
        countries=_normalize_multiselect(countries),
        release_year_range=(release_year_range[0], release_year_range[1]),
        date_added_range=(
            date_added_range[0] if isinstance(date_added_range, tuple) else date_min,
            date_added_range[1] if isinstance(date_added_range, tuple) else date_max,
        ),
        title_search=title_search.strip() or None,
    )

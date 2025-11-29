"""Parameterized SQL helpers for the dashboard views."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Sequence, Tuple

import pandas as pd

# from .db import run_query
# from .filters import FilterOptions, FilterState

from db import run_query
from filters import FilterOptions, FilterState

@dataclass(frozen=True)
class FilterMetadata:
    """Derived min/max metadata for initializing UI controls."""

    release_year_bounds: tuple[int | None, int | None]
    date_added_bounds: tuple[date | None, date | None]


def fetch_filter_options() -> FilterOptions:
    """Pull distinct filter values from the database."""

    services = run_query(
        "SELECT service_name FROM streaming_service ORDER BY service_name"
    )["service_name"].tolist()

    genres = run_query(
        "SELECT genre_name FROM genre ORDER BY genre_name"
    )["genre_name"].tolist()

    countries = run_query(
        "SELECT country_name FROM country ORDER BY country_name"
    )["country_name"].tolist()

    release_bounds_df = run_query(
        "SELECT MIN(release_year) AS min_year, MAX(release_year) AS max_year FROM title"
    )
    release_bounds = (
        int(release_bounds_df.at[0, "min_year"]) if pd.notna(release_bounds_df.at[0, "min_year"]) else None,
        int(release_bounds_df.at[0, "max_year"]) if pd.notna(release_bounds_df.at[0, "max_year"]) else None,
    )

    date_bounds_df = run_query(
        "SELECT MIN(date_added) AS min_date, MAX(date_added) AS max_date FROM streaming_availability"
    )
    min_date = (
        pd.to_datetime(date_bounds_df.at[0, "min_date"]).date()
        if pd.notna(date_bounds_df.at[0, "min_date"])
        else None
    )
    max_date = (
        pd.to_datetime(date_bounds_df.at[0, "max_date"]).date()
        if pd.notna(date_bounds_df.at[0, "max_date"])
        else None
    )

    return FilterOptions(
        services=services,
        content_types=("MOVIE", "TV_SHOW"),
        genres=genres,
        countries=countries,
        release_year_bounds=release_bounds,
        date_added_bounds=(min_date, max_date),
    )


# ---------------------------------------------------------------------------
# WHERE clause builder
# ---------------------------------------------------------------------------

def _build_where_clause(filters: FilterState | None) -> tuple[str, List[object]]:
    if not filters:
        return "", []

    clauses: List[str] = []
    params: List[object] = []

    if filters.services:
        placeholders = ", ".join(["%s"] * len(filters.services))
        clauses.append(f"ss.service_name IN ({placeholders})")
        params.extend(filters.services)

    if filters.content_types:
        placeholders = ", ".join(["%s"] * len(filters.content_types))
        clauses.append(f"t.content_type IN ({placeholders})")
        params.extend(filters.content_types)

    if filters.genres:
        placeholders = ", ".join(["%s"] * len(filters.genres))
        clauses.append(
            "EXISTS (SELECT 1 FROM title_genre tg JOIN genre g ON g.genre_id = tg.genre_id "
            "WHERE tg.title_id = t.title_id AND g.genre_name IN (" + placeholders + "))"
        )
        params.extend(filters.genres)

    if filters.countries:
        placeholders = ", ".join(["%s"] * len(filters.countries))
        clauses.append(
            "EXISTS (SELECT 1 FROM title_country tc JOIN country c ON c.country_id = tc.country_id "
            "WHERE tc.title_id = t.title_id AND c.country_name IN (" + placeholders + "))"
        )
        params.extend(filters.countries)

    release_start, release_end = filters.release_year_range
    if release_start is not None and release_end is not None:
        clauses.append("t.release_year BETWEEN %s AND %s")
        params.extend([release_start, release_end])

    date_start, date_end = filters.date_added_range
    if date_start is not None and date_end is not None:
        clauses.append("sa.date_added BETWEEN %s AND %s")
        params.extend([date_start, date_end])

    if filters.title_search:
        clauses.append("t.global_title_name LIKE %s")
        params.append(f"%{filters.title_search}%")

    if not clauses:
        return "", params

    return "WHERE " + " AND ".join(clauses), params


# ---------------------------------------------------------------------------
# Query helpers exposed to sections
# ---------------------------------------------------------------------------

def fetch_overview_metrics(filters: FilterState | None) -> pd.DataFrame:
    where_clause, params = _build_where_clause(filters)
    sql = f"""
        SELECT
            COUNT(DISTINCT t.title_id) AS total_titles,
            SUM(CASE WHEN t.content_type = 'MOVIE' THEN 1 ELSE 0 END) AS movie_count,
            SUM(CASE WHEN t.content_type = 'TV_SHOW' THEN 1 ELSE 0 END) AS tv_show_count,
            COUNT(DISTINCT g.genre_id) AS distinct_genres,
            COUNT(DISTINCT c.country_id) AS distinct_countries
        FROM title t
        JOIN streaming_availability sa ON sa.title_id = t.title_id
        JOIN streaming_service ss ON ss.streaming_service_id = sa.streaming_service_id
        LEFT JOIN title_genre tg ON tg.title_id = t.title_id
        LEFT JOIN genre g ON g.genre_id = tg.genre_id
        LEFT JOIN title_country tc ON tc.title_id = t.title_id
        LEFT JOIN country c ON c.country_id = tc.country_id
        {where_clause}
    """
    return run_query(sql, params)


def fetch_platform_breakdown(filters: FilterState | None) -> pd.DataFrame:
    where_clause, params = _build_where_clause(filters)
    sql = f"""
        SELECT
            ss.service_name,
            COUNT(DISTINCT t.title_id) AS total_titles,
            SUM(CASE WHEN t.content_type = 'MOVIE' THEN 1 ELSE 0 END) AS movie_count,
            SUM(CASE WHEN t.content_type = 'TV_SHOW' THEN 1 ELSE 0 END) AS tv_show_count
        FROM title t
        JOIN streaming_availability sa ON sa.title_id = t.title_id
        JOIN streaming_service ss ON ss.streaming_service_id = sa.streaming_service_id
        {where_clause}
        GROUP BY ss.service_name
        ORDER BY total_titles DESC
    """
    return run_query(sql, params)


def fetch_genre_distribution(filters: FilterState | None) -> pd.DataFrame:
    where_clause, params = _build_where_clause(filters)
    sql = f"""
        SELECT
            ss.service_name,
            g.genre_name,
            COUNT(DISTINCT t.title_id) AS title_count
        FROM title t
        JOIN streaming_availability sa ON sa.title_id = t.title_id
        JOIN streaming_service ss ON ss.streaming_service_id = sa.streaming_service_id
        JOIN title_genre tg ON tg.title_id = t.title_id
        JOIN genre g ON g.genre_id = tg.genre_id
        {where_clause}
        GROUP BY ss.service_name, g.genre_name
        ORDER BY title_count DESC
    """
    return run_query(sql, params)


def fetch_country_distribution(filters: FilterState | None) -> pd.DataFrame:
    where_clause, params = _build_where_clause(filters)
    sql = f"""
        SELECT
            c.country_name,
            COUNT(DISTINCT t.title_id) AS title_count
        FROM title t
        JOIN streaming_availability sa ON sa.title_id = t.title_id
        JOIN streaming_service ss ON ss.streaming_service_id = sa.streaming_service_id
        JOIN title_country tc ON tc.title_id = t.title_id
        JOIN country c ON c.country_id = tc.country_id
        {where_clause}
        GROUP BY c.country_name
        ORDER BY title_count DESC
    """
    return run_query(sql, params)


def fetch_release_year_trend(filters: FilterState | None) -> pd.DataFrame:
    where_clause, params = _build_where_clause(filters)
    sql = f"""
        SELECT
            t.release_year,
            ss.service_name,
            COUNT(DISTINCT t.title_id) AS title_count
        FROM title t
        JOIN streaming_availability sa ON sa.title_id = t.title_id
        JOIN streaming_service ss ON ss.streaming_service_id = sa.streaming_service_id
        {where_clause}
        GROUP BY t.release_year, ss.service_name
        ORDER BY t.release_year ASC
    """
    return run_query(sql, params)


def fetch_date_added_trend(filters: FilterState | None) -> pd.DataFrame:
    where_clause, params = _build_where_clause(filters)
    sql = f"""
        SELECT
            DATE_FORMAT(sa.date_added, '%Y-%m-01') AS month_bucket,
            ss.service_name,
            COUNT(DISTINCT t.title_id) AS title_count
        FROM title t
        JOIN streaming_availability sa ON sa.title_id = t.title_id
        JOIN streaming_service ss ON ss.streaming_service_id = sa.streaming_service_id
        WHERE sa.date_added IS NOT NULL
        {(' AND ' + where_clause[6:]) if where_clause else ''}
        GROUP BY month_bucket, ss.service_name
        ORDER BY month_bucket ASC
    """
    return run_query(sql, params)


def fetch_titles_table(filters: FilterState | None, limit: int = 250) -> pd.DataFrame:
    where_clause, params = _build_where_clause(filters)
    sql = f"""
        SELECT
            t.global_title_name AS title,
            t.content_type,
            t.release_year,
            GROUP_CONCAT(DISTINCT g.genre_name ORDER BY g.genre_name SEPARATOR ', ') AS genres,
            GROUP_CONCAT(DISTINCT c.country_name ORDER BY c.country_name SEPARATOR ', ') AS countries,
            ss.service_name,
            sa.date_added
        FROM title t
        JOIN streaming_availability sa ON sa.title_id = t.title_id
        JOIN streaming_service ss ON ss.streaming_service_id = sa.streaming_service_id
        LEFT JOIN title_genre tg ON tg.title_id = t.title_id
        LEFT JOIN genre g ON g.genre_id = tg.genre_id
        LEFT JOIN title_country tc ON tc.title_id = t.title_id
        LEFT JOIN country c ON c.country_id = tc.country_id
        {where_clause}
        GROUP BY t.title_id, ss.service_name, sa.date_added
        ORDER BY sa.date_added DESC
        LIMIT %s
    """
    return run_query(sql, params + [limit])


def fetch_similarity_candidates(filters: FilterState | None, title_keyword: str) -> pd.DataFrame:
    """Simple content-based similarity placeholder using shared genres."""

    where_clause, params = _build_where_clause(filters)
    sql = f"""
        SELECT
            other.global_title_name AS title,
            other.release_year,
            ss.service_name,
            COUNT(*) AS shared_genres
        FROM title anchor
        JOIN title_genre atg ON atg.title_id = anchor.title_id
        JOIN title_genre otg ON otg.genre_id = atg.genre_id
        JOIN title other ON other.title_id = otg.title_id
        JOIN streaming_availability sa ON sa.title_id = other.title_id
        JOIN streaming_service ss ON ss.streaming_service_id = sa.streaming_service_id
        WHERE anchor.global_title_name LIKE %s
          AND other.title_id <> anchor.title_id
          {(' AND ' + where_clause[6:]) if where_clause else ''}
        GROUP BY other.title_id, ss.service_name
        ORDER BY shared_genres DESC, other.release_year DESC
        LIMIT 25
    """
    return run_query(sql, [f"%{title_keyword}%", *params])

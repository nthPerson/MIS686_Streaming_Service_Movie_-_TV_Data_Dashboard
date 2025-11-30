"""SQLAlchemy-powered data access helpers for the dashboard."""

from __future__ import annotations

from datetime import datetime
from typing import List

import pandas as pd
from sqlalchemy import and_, case, distinct, func, select
from sqlalchemy.orm import aliased

from db import get_session
from filters import FilterOptions, FilterState
from models import (
    Country,
    Genre,
    StreamingAvailability,
    StreamingService,
    Title,
    TitleCountry,
    TitleGenre,
)


def _to_dataframe(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def _execute_statement(statement) -> pd.DataFrame:
    with get_session() as session:
        result = session.execute(statement)
        rows = result.mappings().all()
    return _to_dataframe(rows)


def _normalize_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    return value


def fetch_filter_options() -> FilterOptions:
    with get_session() as session:
        services = session.scalars(
            select(StreamingService.service_name).order_by(StreamingService.service_name)
        ).all()
        genres = session.scalars(select(Genre.genre_name).order_by(Genre.genre_name)).all()
        countries = session.scalars(select(Country.country_name).order_by(Country.country_name)).all()

        release_bounds = session.execute(
            select(func.min(Title.release_year).label("min_year"), func.max(Title.release_year).label("max_year"))
        ).one()

        date_bounds = session.execute(
            select(
                func.min(StreamingAvailability.date_added).label("min_date"),
                func.max(StreamingAvailability.date_added).label("max_date"),
            )
        ).one()

    min_release = int(release_bounds.min_year) if release_bounds.min_year is not None else None
    max_release = int(release_bounds.max_year) if release_bounds.max_year is not None else None

    min_date = _normalize_date(date_bounds.min_date)
    max_date = _normalize_date(date_bounds.max_date)

    return FilterOptions(
        services=services,
        content_types=("MOVIE", "TV_SHOW"),
        genres=genres,
        countries=countries,
        release_year_bounds=(min_release, max_release),
        date_added_bounds=(min_date, max_date),
    )


def _build_filters(
    filters: FilterState | None,
    *,
    title_entity=Title,
    availability_entity=StreamingAvailability,
    service_entity=StreamingService,
):
    if not filters:
        return []

    conditions: List = []

    if filters.services:
        conditions.append(service_entity.service_name.in_(filters.services))

    if filters.content_types:
        conditions.append(title_entity.content_type.in_(filters.content_types))

    if filters.genres:
        tg = aliased(TitleGenre)
        g = aliased(Genre)
        genre_exists = (
            select(1)
            .select_from(tg)
            .join(g, tg.genre_id == g.genre_id)
            .where(tg.title_id == title_entity.title_id, g.genre_name.in_(filters.genres))
            .exists()
        )
        conditions.append(genre_exists)

    if filters.countries:
        tc = aliased(TitleCountry)
        c = aliased(Country)
        country_exists = (
            select(1)
            .select_from(tc)
            .join(c, tc.country_id == c.country_id)
            .where(tc.title_id == title_entity.title_id, c.country_name.in_(filters.countries))
            .exists()
        )
        conditions.append(country_exists)

    release_start, release_end = filters.release_year_range
    if release_start is not None and release_end is not None:
        conditions.append(title_entity.release_year.between(release_start, release_end))

    date_start, date_end = filters.date_added_range
    if date_start is not None and date_end is not None:
        conditions.append(availability_entity.date_added.between(date_start, date_end))

    if filters.title_search:
        conditions.append(title_entity.global_title_name.ilike(f"%{filters.title_search}%"))

    return conditions


def fetch_overview_metrics(filters: FilterState | None) -> pd.DataFrame:
    conditions = _build_filters(filters)

    stmt = (
        select(
            func.count(distinct(Title.title_id)).label("total_titles"),
            func.sum(case((Title.content_type == "MOVIE", 1), else_=0)).label("movie_count"),
            func.sum(case((Title.content_type == "TV_SHOW", 1), else_=0)).label("tv_show_count"),
            func.count(distinct(Genre.genre_id)).label("distinct_genres"),
            func.count(distinct(Country.country_id)).label("distinct_countries"),
        )
        .join(StreamingAvailability, StreamingAvailability.title_id == Title.title_id)
        .join(StreamingService, StreamingService.streaming_service_id == StreamingAvailability.streaming_service_id)
        .outerjoin(TitleGenre, TitleGenre.title_id == Title.title_id)
        .outerjoin(Genre, Genre.genre_id == TitleGenre.genre_id)
        .outerjoin(TitleCountry, TitleCountry.title_id == Title.title_id)
        .outerjoin(Country, Country.country_id == TitleCountry.country_id)
    )

    if conditions:
        stmt = stmt.where(and_(*conditions))

    return _execute_statement(stmt)


def fetch_platform_breakdown(filters: FilterState | None) -> pd.DataFrame:
    conditions = _build_filters(filters)

    stmt = (
        select(
            StreamingService.service_name,
            func.count(distinct(Title.title_id)).label("total_titles"),
            func.sum(case((Title.content_type == "MOVIE", 1), else_=0)).label("movie_count"),
            func.sum(case((Title.content_type == "TV_SHOW", 1), else_=0)).label("tv_show_count"),
        )
        .join(StreamingAvailability, StreamingAvailability.title_id == Title.title_id)
        .join(StreamingService, StreamingService.streaming_service_id == StreamingAvailability.streaming_service_id)
        .group_by(StreamingService.service_name)
        .order_by(func.count(distinct(Title.title_id)).desc())
    )

    if conditions:
        stmt = stmt.where(and_(*conditions))

    return _execute_statement(stmt)


def fetch_genre_distribution(filters: FilterState | None) -> pd.DataFrame:
    conditions = _build_filters(filters)

    stmt = (
        select(
            StreamingService.service_name,
            Genre.genre_name,
            func.count(distinct(Title.title_id)).label("title_count"),
        )
        .join(StreamingAvailability, StreamingAvailability.title_id == Title.title_id)
        .join(StreamingService, StreamingService.streaming_service_id == StreamingAvailability.streaming_service_id)
        .join(TitleGenre, TitleGenre.title_id == Title.title_id)
        .join(Genre, Genre.genre_id == TitleGenre.genre_id)
        .group_by(StreamingService.service_name, Genre.genre_name)
        .order_by(func.count(distinct(Title.title_id)).desc())
    )

    if conditions:
        stmt = stmt.where(and_(*conditions))

    return _execute_statement(stmt)


def fetch_country_distribution(filters: FilterState | None) -> pd.DataFrame:
    conditions = _build_filters(filters)

    stmt = (
        select(
            Country.country_name,
            func.count(distinct(Title.title_id)).label("title_count"),
        )
        .join(StreamingAvailability, StreamingAvailability.title_id == Title.title_id)
        .join(TitleCountry, TitleCountry.title_id == Title.title_id)
        .join(Country, Country.country_id == TitleCountry.country_id)
        .group_by(Country.country_name)
        .order_by(func.count(distinct(Title.title_id)).desc())
    )

    if conditions:
        stmt = stmt.where(and_(*conditions))

    return _execute_statement(stmt)


def fetch_release_year_trend(filters: FilterState | None) -> pd.DataFrame:
    conditions = _build_filters(filters)

    stmt = (
        select(
            Title.release_year,
            StreamingService.service_name,
            func.count(distinct(Title.title_id)).label("title_count"),
        )
        .join(StreamingAvailability, StreamingAvailability.title_id == Title.title_id)
        .join(StreamingService, StreamingService.streaming_service_id == StreamingAvailability.streaming_service_id)
        .group_by(Title.release_year, StreamingService.service_name)
        .order_by(Title.release_year.asc())
    )

    if conditions:
        stmt = stmt.where(and_(*conditions))

    return _execute_statement(stmt)


def fetch_date_added_trend(filters: FilterState | None) -> pd.DataFrame:
    conditions = _build_filters(filters)
    conditions.append(StreamingAvailability.date_added.is_not(None))

    month_bucket = func.date_format(StreamingAvailability.date_added, "%Y-%m-01").label("month_bucket")

    stmt = (
        select(
            month_bucket,
            StreamingService.service_name,
            func.count(distinct(Title.title_id)).label("title_count"),
        )
        .join(StreamingAvailability, StreamingAvailability.title_id == Title.title_id)
        .join(StreamingService, StreamingService.streaming_service_id == StreamingAvailability.streaming_service_id)
        .group_by(month_bucket, StreamingService.service_name)
        .order_by(month_bucket)
    )

    if conditions:
        stmt = stmt.where(and_(*conditions))

    return _execute_statement(stmt)


def fetch_titles_table(filters: FilterState | None, limit: int = 250) -> pd.DataFrame:
    conditions = _build_filters(filters)

    stmt = (
        select(
            Title.global_title_name.label("title"),
            Title.content_type,
            Title.release_year,
            func.group_concat(distinct(Genre.genre_name)).label("genres"),
            func.group_concat(distinct(Country.country_name)).label("countries"),
            StreamingService.service_name,
            StreamingAvailability.date_added,
        )
        .join(StreamingAvailability, StreamingAvailability.title_id == Title.title_id)
        .join(StreamingService, StreamingService.streaming_service_id == StreamingAvailability.streaming_service_id)
        .outerjoin(TitleGenre, TitleGenre.title_id == Title.title_id)
        .outerjoin(Genre, Genre.genre_id == TitleGenre.genre_id)
        .outerjoin(TitleCountry, TitleCountry.title_id == Title.title_id)
        .outerjoin(Country, Country.country_id == TitleCountry.country_id)
        .group_by(Title.title_id, StreamingService.service_name, StreamingAvailability.date_added)
        .order_by(StreamingAvailability.date_added.desc())
        .limit(limit)
    )

    if conditions:
        stmt = stmt.where(and_(*conditions))

    return _execute_statement(stmt)


def fetch_similarity_candidates(filters: FilterState | None, title_keyword: str) -> pd.DataFrame:
    other_title = aliased(Title)
    other_availability = aliased(StreamingAvailability)
    other_service = aliased(StreamingService)

    conditions = _build_filters(
        filters,
        title_entity=other_title,
        availability_entity=other_availability,
        service_entity=other_service,
    )

    anchor_title = aliased(Title)
    anchor_tg = aliased(TitleGenre)
    other_tg = aliased(TitleGenre)

    stmt = (
        select(
            other_title.global_title_name.label("title"),
            other_title.release_year,
            other_service.service_name,
            func.count().label("shared_genres"),
        )
        .join_from(other_title, other_tg, other_tg.title_id == other_title.title_id)
        .join(anchor_tg, anchor_tg.genre_id == other_tg.genre_id)
        .join(anchor_title, anchor_title.title_id == anchor_tg.title_id)
        .join(other_availability, other_availability.title_id == other_title.title_id)
        .join(other_service, other_service.streaming_service_id == other_availability.streaming_service_id)
        .where(anchor_title.global_title_name.ilike(f"%{title_keyword}%"))
        .where(other_title.title_id != anchor_title.title_id)
        .group_by(other_title.title_id, other_service.service_name)
        .order_by(func.count().desc(), other_title.release_year.desc())
        .limit(25)
    )

    if conditions:
        stmt = stmt.where(and_(*conditions))

    return _execute_statement(stmt)



## This is the beginning of the original queries.py
#"""Parameterized SQL helpers for the dashboard views."""
# from __future__ import annotations

# from dataclasses import dataclass
# from datetime import date
# from typing import List, Sequence, Tuple

# import pandas as pd
# from db import run_query
# from filters import FilterOptions, FilterState

# @dataclass(frozen=True)
# class FilterMetadata:
#     """Derived min/max metadata for initializing UI controls."""

#     release_year_bounds: tuple[int | None, int | None]
#     date_added_bounds: tuple[date | None, date | None]


# def fetch_filter_options() -> FilterOptions:
#     """Pull distinct filter values from the database."""

#     services = run_query(
#         "SELECT service_name FROM streaming_service ORDER BY service_name"
#     )["service_name"].tolist()

#     genres = run_query(
#         "SELECT genre_name FROM genre ORDER BY genre_name"
#     )["genre_name"].tolist()

#     countries = run_query(
#         "SELECT country_name FROM country ORDER BY country_name"
#     )["country_name"].tolist()

#     release_bounds_df = run_query(
#         "SELECT MIN(release_year) AS min_year, MAX(release_year) AS max_year FROM title"
#     )
#     release_bounds = (
#         int(release_bounds_df.at[0, "min_year"]) if pd.notna(release_bounds_df.at[0, "min_year"]) else None,
#         int(release_bounds_df.at[0, "max_year"]) if pd.notna(release_bounds_df.at[0, "max_year"]) else None,
#     )

#     date_bounds_df = run_query(
#         "SELECT MIN(date_added) AS min_date, MAX(date_added) AS max_date FROM streaming_availability"
#     )
#     min_date = (
#         pd.to_datetime(date_bounds_df.at[0, "min_date"]).date()
#         if pd.notna(date_bounds_df.at[0, "min_date"])
#         else None
#     )
#     max_date = (
#         pd.to_datetime(date_bounds_df.at[0, "max_date"]).date()
#         if pd.notna(date_bounds_df.at[0, "max_date"])
#         else None
#     )

#     return FilterOptions(
#         services=services,
#         content_types=("MOVIE", "TV_SHOW"),
#         genres=genres,
#         countries=countries,
#         release_year_bounds=release_bounds,
#         date_added_bounds=(min_date, max_date),
#     )


# # ---------------------------------------------------------------------------
# # WHERE clause builder
# # ---------------------------------------------------------------------------

# def _build_where_clause(filters: FilterState | None) -> tuple[str, List[object]]:
#     if not filters:
#         return "", []

#     clauses: List[str] = []
#     params: List[object] = []

#     if filters.services:
#         placeholders = ", ".join(["%s"] * len(filters.services))
#         clauses.append(f"ss.service_name IN ({placeholders})")
#         params.extend(filters.services)

#     if filters.content_types:
#         placeholders = ", ".join(["%s"] * len(filters.content_types))
#         clauses.append(f"t.content_type IN ({placeholders})")
#         params.extend(filters.content_types)

#     if filters.genres:
#         placeholders = ", ".join(["%s"] * len(filters.genres))
#         clauses.append(
#             "EXISTS (SELECT 1 FROM title_genre tg JOIN genre g ON g.genre_id = tg.genre_id "
#             "WHERE tg.title_id = t.title_id AND g.genre_name IN (" + placeholders + "))"
#         )
#         params.extend(filters.genres)

#     if filters.countries:
#         placeholders = ", ".join(["%s"] * len(filters.countries))
#         clauses.append(
#             "EXISTS (SELECT 1 FROM title_country tc JOIN country c ON c.country_id = tc.country_id "
#             "WHERE tc.title_id = t.title_id AND c.country_name IN (" + placeholders + "))"
#         )
#         params.extend(filters.countries)

#     release_start, release_end = filters.release_year_range
#     if release_start is not None and release_end is not None:
#         clauses.append("t.release_year BETWEEN %s AND %s")
#         params.extend([release_start, release_end])

#     date_start, date_end = filters.date_added_range
#     if date_start is not None and date_end is not None:
#         clauses.append("sa.date_added BETWEEN %s AND %s")
#         params.extend([date_start, date_end])

#     if filters.title_search:
#         clauses.append("t.global_title_name LIKE %s")
#         params.append(f"%{filters.title_search}%")

#     if not clauses:
#         return "", params

#     return "WHERE " + " AND ".join(clauses), params


# # ---------------------------------------------------------------------------
# # Query helpers exposed to sections
# # ---------------------------------------------------------------------------

# def fetch_overview_metrics(filters: FilterState | None) -> pd.DataFrame:
#     where_clause, params = _build_where_clause(filters)
#     sql = f"""
#         SELECT
#             COUNT(DISTINCT t.title_id) AS total_titles,
#             SUM(CASE WHEN t.content_type = 'MOVIE' THEN 1 ELSE 0 END) AS movie_count,
#             SUM(CASE WHEN t.content_type = 'TV_SHOW' THEN 1 ELSE 0 END) AS tv_show_count,
#             COUNT(DISTINCT g.genre_id) AS distinct_genres,
#             COUNT(DISTINCT c.country_id) AS distinct_countries
#         FROM title t
#         JOIN streaming_availability sa ON sa.title_id = t.title_id
#         JOIN streaming_service ss ON ss.streaming_service_id = sa.streaming_service_id
#         LEFT JOIN title_genre tg ON tg.title_id = t.title_id
#         LEFT JOIN genre g ON g.genre_id = tg.genre_id
#         LEFT JOIN title_country tc ON tc.title_id = t.title_id
#         LEFT JOIN country c ON c.country_id = tc.country_id
#         {where_clause}
#     """
#     return run_query(sql, params)


# def fetch_platform_breakdown(filters: FilterState | None) -> pd.DataFrame:
#     where_clause, params = _build_where_clause(filters)
#     sql = f"""
#         SELECT
#             ss.service_name,
#             COUNT(DISTINCT t.title_id) AS total_titles,
#             SUM(CASE WHEN t.content_type = 'MOVIE' THEN 1 ELSE 0 END) AS movie_count,
#             SUM(CASE WHEN t.content_type = 'TV_SHOW' THEN 1 ELSE 0 END) AS tv_show_count
#         FROM title t
#         JOIN streaming_availability sa ON sa.title_id = t.title_id
#         JOIN streaming_service ss ON ss.streaming_service_id = sa.streaming_service_id
#         {where_clause}
#         GROUP BY ss.service_name
#         ORDER BY total_titles DESC
#     """
#     return run_query(sql, params)


# def fetch_genre_distribution(filters: FilterState | None) -> pd.DataFrame:
#     where_clause, params = _build_where_clause(filters)
#     sql = f"""
#         SELECT
#             ss.service_name,
#             g.genre_name,
#             COUNT(DISTINCT t.title_id) AS title_count
#         FROM title t
#         JOIN streaming_availability sa ON sa.title_id = t.title_id
#         JOIN streaming_service ss ON ss.streaming_service_id = sa.streaming_service_id
#         JOIN title_genre tg ON tg.title_id = t.title_id
#         JOIN genre g ON g.genre_id = tg.genre_id
#         {where_clause}
#         GROUP BY ss.service_name, g.genre_name
#         ORDER BY title_count DESC
#     """
#     return run_query(sql, params)


# def fetch_country_distribution(filters: FilterState | None) -> pd.DataFrame:
#     where_clause, params = _build_where_clause(filters)
#     sql = f"""
#         SELECT
#             c.country_name,
#             COUNT(DISTINCT t.title_id) AS title_count
#         FROM title t
#         JOIN streaming_availability sa ON sa.title_id = t.title_id
#         JOIN streaming_service ss ON ss.streaming_service_id = sa.streaming_service_id
#         JOIN title_country tc ON tc.title_id = t.title_id
#         JOIN country c ON c.country_id = tc.country_id
#         {where_clause}
#         GROUP BY c.country_name
#         ORDER BY title_count DESC
#     """
#     return run_query(sql, params)


# def fetch_release_year_trend(filters: FilterState | None) -> pd.DataFrame:
#     where_clause, params = _build_where_clause(filters)
#     sql = f"""
#         SELECT
#             t.release_year,
#             ss.service_name,
#             COUNT(DISTINCT t.title_id) AS title_count
#         FROM title t
#         JOIN streaming_availability sa ON sa.title_id = t.title_id
#         JOIN streaming_service ss ON ss.streaming_service_id = sa.streaming_service_id
#         {where_clause}
#         GROUP BY t.release_year, ss.service_name
#         ORDER BY t.release_year ASC
#     """
#     return run_query(sql, params)


# def fetch_date_added_trend(filters: FilterState | None) -> pd.DataFrame:
#     where_clause, params = _build_where_clause(filters)
#     sql = f"""
#         SELECT
#             DATE_FORMAT(sa.date_added, '%Y-%m-01') AS month_bucket,
#             ss.service_name,
#             COUNT(DISTINCT t.title_id) AS title_count
#         FROM title t
#         JOIN streaming_availability sa ON sa.title_id = t.title_id
#         JOIN streaming_service ss ON ss.streaming_service_id = sa.streaming_service_id
#         WHERE sa.date_added IS NOT NULL
#         {(' AND ' + where_clause[6:]) if where_clause else ''}
#         GROUP BY month_bucket, ss.service_name
#         ORDER BY month_bucket ASC
#     """
#     return run_query(sql, params)


# def fetch_titles_table(filters: FilterState | None, limit: int = 250) -> pd.DataFrame:
#     where_clause, params = _build_where_clause(filters)
#     sql = f"""
#         SELECT
#             t.global_title_name AS title,
#             t.content_type,
#             t.release_year,
#             GROUP_CONCAT(DISTINCT g.genre_name ORDER BY g.genre_name SEPARATOR ', ') AS genres,
#             GROUP_CONCAT(DISTINCT c.country_name ORDER BY c.country_name SEPARATOR ', ') AS countries,
#             ss.service_name,
#             sa.date_added
#         FROM title t
#         JOIN streaming_availability sa ON sa.title_id = t.title_id
#         JOIN streaming_service ss ON ss.streaming_service_id = sa.streaming_service_id
#         LEFT JOIN title_genre tg ON tg.title_id = t.title_id
#         LEFT JOIN genre g ON g.genre_id = tg.genre_id
#         LEFT JOIN title_country tc ON tc.title_id = t.title_id
#         LEFT JOIN country c ON c.country_id = tc.country_id
#         {where_clause}
#         GROUP BY t.title_id, ss.service_name, sa.date_added
#         ORDER BY sa.date_added DESC
#         LIMIT %s
#     """
#     return run_query(sql, params + [limit])


# def fetch_similarity_candidates(filters: FilterState | None, title_keyword: str) -> pd.DataFrame:
#     """Simple content-based similarity placeholder using shared genres."""

#     where_clause, params = _build_where_clause(filters)
#     sql = f"""
#         SELECT
#             other.global_title_name AS title,
#             other.release_year,
#             ss.service_name,
#             COUNT(*) AS shared_genres
#         FROM title anchor
#         JOIN title_genre atg ON atg.title_id = anchor.title_id
#         JOIN title_genre otg ON otg.genre_id = atg.genre_id
#         JOIN title other ON other.title_id = otg.title_id
#         JOIN streaming_availability sa ON sa.title_id = other.title_id
#         JOIN streaming_service ss ON ss.streaming_service_id = sa.streaming_service_id
#         WHERE anchor.global_title_name LIKE %s
#           AND other.title_id <> anchor.title_id
#           {(' AND ' + where_clause[6:]) if where_clause else ''}
#         GROUP BY other.title_id, ss.service_name
#         ORDER BY shared_genres DESC, other.release_year DESC
#         LIMIT 25
#     """
#     return run_query(sql, [f"%{title_keyword}%", *params])

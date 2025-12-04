"""Question-focused landing sections for the main dashboard."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

import queries

Q1_SQL = """
SELECT
    ss.service_name,
    COUNT(DISTINCT t.title_id) AS total_titles
FROM streaming_service AS ss
JOIN streaming_availability AS sa ON sa.streaming_service_id = ss.streaming_service_id
JOIN title AS t ON t.title_id = sa.title_id
GROUP BY ss.service_name
ORDER BY total_titles DESC;
"""

Q2_SQL = """
SELECT
    ss.service_name,
    SUM(CASE WHEN t.content_type = 'MOVIE' THEN 1 ELSE 0 END) AS movie_count,
    SUM(CASE WHEN t.content_type = 'TV_SHOW' THEN 1 ELSE 0 END) AS tv_show_count
FROM streaming_service AS ss
JOIN streaming_availability AS sa ON sa.streaming_service_id = ss.streaming_service_id
JOIN title AS t ON t.title_id = sa.title_id
GROUP BY ss.service_name
ORDER BY ss.service_name;
"""

Q3_SQL = """
SELECT
    ss.service_name,
    COUNT(DISTINCT c.country_id) AS countries_represented
FROM streaming_service AS ss
JOIN streaming_availability AS sa ON sa.streaming_service_id = ss.streaming_service_id
JOIN title AS t ON t.title_id = sa.title_id
JOIN title_country AS tc ON tc.title_id = t.title_id
JOIN country AS c ON c.country_id = tc.country_id
GROUP BY ss.service_name
ORDER BY countries_represented DESC;
"""

Q4_SQL = """
SELECT
    c.country_name,
    COUNT(DISTINCT t.title_id) AS title_count
FROM country AS c
JOIN title_country AS tc ON tc.country_id = c.country_id
JOIN title AS t ON t.title_id = tc.title_id
JOIN streaming_availability AS sa ON sa.title_id = t.title_id
GROUP BY c.country_name
ORDER BY title_count DESC;
"""

Q5_SQL = """
SELECT
    g.genre_name,
    COUNT(DISTINCT t.title_id) AS title_count
FROM genre AS g
JOIN title_genre AS tg ON tg.genre_id = g.genre_id
JOIN title AS t ON t.title_id = tg.title_id
JOIN streaming_availability AS sa ON sa.title_id = t.title_id
GROUP BY g.genre_name
ORDER BY title_count DESC;
"""

Q6_SQL = """
WITH genre_service AS (
    SELECT
        g.genre_name,
        ss.service_name,
        COUNT(DISTINCT t.title_id) AS title_count
    FROM title AS t
    JOIN streaming_availability AS sa ON sa.title_id = t.title_id
    JOIN streaming_service AS ss ON ss.streaming_service_id = sa.streaming_service_id
    JOIN title_genre AS tg ON tg.title_id = t.title_id
    JOIN genre AS g ON g.genre_id = tg.genre_id
    GROUP BY g.genre_name, ss.service_name
)
SELECT
    genre_name,
    service_name,
    title_count,
    title_count / SUM(title_count) OVER (PARTITION BY genre_name) AS service_share
FROM genre_service
ORDER BY genre_name, service_share DESC;
"""

Q7_SQL = """
SELECT
    ss.service_name,
    CASE
        WHEN UPPER(t.age_rating_code) IN ('G','TV-G','TV-Y','Y') THEN 'G'
        WHEN UPPER(t.age_rating_code) IN ('PG','TV-PG','TV-Y7','TV-Y7-FV') THEN 'PG'
        WHEN UPPER(t.age_rating_code) IN ('PG-13','TV-14') THEN 'PG-13'
        WHEN UPPER(t.age_rating_code) IN ('R','NC-17','TV-MA') THEN 'R/TV-MA'
        ELSE 'Unrated/Other'
    END AS rating_bucket,
    COUNT(DISTINCT t.title_id) AS title_count
FROM streaming_service AS ss
JOIN streaming_availability AS sa ON sa.streaming_service_id = ss.streaming_service_id
JOIN title AS t ON t.title_id = sa.title_id
GROUP BY ss.service_name, rating_bucket
ORDER BY ss.service_name, rating_bucket;
"""

Q8_SQL = """
SELECT
    ss.service_name,
    CASE
        WHEN UPPER(t.age_rating_code) IN ('G','TV-G','TV-Y','Y','PG','TV-PG','TV-Y7','TV-Y7-FV') THEN 'Family (G/PG)'
        WHEN UPPER(t.age_rating_code) IN ('PG-13','TV-14','R','NC-17','TV-MA') THEN 'Mature (PG-13+/R)'
        ELSE 'Other / Unrated'
    END AS content_group,
    COUNT(DISTINCT t.title_id) AS title_count
FROM streaming_service AS ss
JOIN streaming_availability AS sa ON sa.streaming_service_id = ss.streaming_service_id
JOIN title AS t ON t.title_id = sa.title_id
GROUP BY ss.service_name, content_group
ORDER BY ss.service_name, content_group;
"""


def render_all() -> None:
    _render_q1()
    st.divider()
    _render_q2()
    st.divider()
    _render_q3()
    st.divider()
    _render_q4()
    st.divider()
    _render_q5()
    st.divider()
    _render_q6()
    st.divider()
    _render_q7()
    st.divider()
    _render_q8()


def _render_q1() -> None:
    st.header("Q1. How many titles does each streaming service offer?")
    df = queries.fetch_platform_breakdown(None)
    if df.empty:
        st.warning("No catalog data is available.")
        return

    services = sorted(df["service_name"].unique())
    selected = st.multiselect(
        "Services to display",
        services,
        default=services,
        key="q1_services",
    )

    if not selected:
        st.info("Select at least one service to render the comparison.")
        return

    filtered = df[df["service_name"].isin(selected)]
    fig = px.bar(
        filtered,
        x="service_name",
        y="total_titles",
        text_auto=".0f",
        labels={"service_name": "Platform", "total_titles": "Titles"},
        title="Total titles per service",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(
        filtered.rename(
            columns={
                "service_name": "Service",
                "total_titles": "Titles",
                "movie_count": "Movies",
                "tv_show_count": "TV Shows",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    with st.expander("SQL query"):
        st.code(Q1_SQL, language="sql")

    with st.expander("Answer / interpretation"):
        st.markdown(_summarize_q1(filtered))


def _render_q2() -> None:
    st.header("Q2. How does the movie/TV show ratio differ across platforms?")
    df = queries.fetch_platform_breakdown(None)
    if df.empty:
        st.warning("No catalog data is available.")
        return

    services = sorted(df["service_name"].unique())
    selected = st.multiselect(
        "Services to compare",
        services,
        default=services,
        key="q2_services",
    )

    if not selected:
        st.info("Select at least one service to compare movie versus TV mixes.")
        return

    filtered = df[df["service_name"].isin(selected)].copy()
    melted = filtered.melt(
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
        # barnorm="percent",
        labels={"service_name": "Platform", "Titles": "Catalog share (count)"},
        title="Relative movie vs TV share (100% stacked)",
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("SQL query"):
        st.code(Q2_SQL, language="sql")

    with st.expander("Answer / interpretation"):
        st.markdown(_summarize_q2(filtered))


def _render_q3() -> None:
    st.header("Q3. How many countries are represented per service?")
    df = queries.fetch_country_diversity_by_service()
    if df.empty:
        st.warning("No country diversity data is available.")
        return

    services = sorted(df["service_name"].unique())
    selected = st.multiselect(
        "Services to display",
        services,
        default=services,
        key="q3_services",
    )

    if not selected:
        st.info("Select at least one service to show country coverage.")
        return

    filtered = df[df["service_name"].isin(selected)]
    fig = px.bar(
        filtered,
        x="service_name",
        y="country_count",
        text_auto=".0f",
        labels={"service_name": "Platform", "country_count": "Countries"},
        title="Distinct production countries per service",
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("SQL query"):
        st.code(Q3_SQL, language="sql")

    with st.expander("Answer / interpretation"):
        st.markdown(_summarize_q3(filtered))


def _render_q4() -> None:
    st.header("Q4. Which countries contribute the most titles across all platforms?")
    df = queries.fetch_country_distribution(None)
    if df.empty:
        st.warning("No country contribution data is available.")
        return

    top_n = st.slider("Top N countries", min_value=5, max_value=25, value=10, key="q4_top")
    filtered = df.head(top_n)
    fig = px.bar(
        filtered,
        x="title_count",
        y="country_name",
        orientation="h",
        text_auto=".0f",
        labels={"country_name": "Country", "title_count": "Titles"},
        title=f"Top {top_n} contributing countries",
    )
    fig.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("SQL query"):
        st.code(Q4_SQL, language="sql")

    with st.expander("Answer / interpretation"):
        st.markdown(_summarize_q4(filtered))


def _render_q5() -> None:
    st.header("Q5. What are the most common genres overall?")
    df = queries.fetch_genre_distribution(None)
    if df.empty:
        st.warning("No genre information is available.")
        return

    genre_totals = (
        df.groupby("genre_name", as_index=False)["title_count"].sum().sort_values("title_count", ascending=False)
    )

    top_n = st.slider("Top genres to highlight", min_value=5, max_value=20, value=10, key="q5_top")
    filtered = genre_totals.head(top_n)

    fig = px.bar(
        filtered,
        x="genre_name",
        y="title_count",
        text_auto=".0f",
        labels={"genre_name": "Genre", "title_count": "Titles"},
        title=f"Top {top_n} genres across all services",
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("SQL query"):
        st.code(Q5_SQL, language="sql")

    with st.expander("Answer / interpretation"):
        st.markdown(_summarize_q5(filtered))


def _render_q6() -> None:
    st.header("Q6. Which genres are most unique or exclusive to individual platforms?")
    df = queries.fetch_genre_uniqueness()
    if df.empty:
        st.warning("No genre uniqueness data is available.")
        return

    threshold = st.slider(
        "Minimum platform share to call a genre near-exclusive",
        min_value=0.3,
        max_value=0.95,
        value=0.6,
        step=0.05,
        key="q6_threshold",
    )
    limit = st.slider("Maximum combinations to list", min_value=5, max_value=25, value=10, key="q6_limit")

    filtered = (
        df[df["service_share"] >= threshold]
        .sort_values("service_share", ascending=False)
        .head(limit)
    )

    if filtered.empty:
        st.info("No genre/service pair crosses the selected exclusivity threshold. Try lowering it.")
    else:
        fig = px.bar(
            filtered,
            x="genre_name",
            y="service_share",
            color="service_name",
            text_auto=".0%",
            labels={"genre_name": "Genre", "service_share": "Share of genre catalog"},
            title="Near-exclusive genre ownership",
        )
        fig.update_layout(yaxis_tickformat="%", xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
        table_df = filtered.copy()
        table_df["service_share"] = pd.to_numeric(table_df["service_share"], errors="coerce")
        table_df = table_df.assign(share_pct=lambda df_: (df_["service_share"] * 100).round(1))
        st.dataframe(
            table_df.rename(columns={"share_pct": "Share (%)", "service_name": "Service"}).drop(
                columns=["service_share"], errors="ignore"
            ),
            use_container_width=True,
            hide_index=True,
        )

    with st.expander("SQL query"):
        st.code(Q6_SQL, language="sql")

    with st.expander("Answer / interpretation"):
        st.markdown(_summarize_q6(filtered, threshold))


def _render_q7() -> None:
    st.header("Q7. How do the streaming services differ in the distribution of maturity ratings?")
    df = queries.fetch_rating_distribution()
    if df.empty:
        st.warning("No maturity rating data is available.")
        return

    services = sorted(df["service_name"].unique())
    selected = st.multiselect(
        "Services to compare",
        services,
        default=services,
        key="q7_services",
    )
    if not selected:
        st.info("Select at least one service to show rating distribution.")
        return

    filtered = df[df["service_name"].isin(selected)].copy()
    if filtered.empty:
        st.info("No records for the selected services.")
        return

    fig = px.bar(
        filtered,
        x="service_name",
        y="title_count",
        color="rating_bucket",
        # barnorm="percent",
        labels={
            "service_name": "Platform",
            "title_count": "Catalog share (count)",
            "rating_bucket": "Rating bucket",
        },
        title="Rating mix per service",
    )
    st.plotly_chart(fig, use_container_width=True)

    filtered["share"] = filtered.groupby("service_name")["title_count"].transform(lambda s: s / s.sum())

    with st.expander("SQL query"):
        st.code(Q7_SQL, language="sql")

    with st.expander("Answer / interpretation"):
        st.markdown(_summarize_q7(filtered))


def _render_q8() -> None:
    st.header(
        "Q8. How do the relative shares of family (G/PG) versus mature (PG-13+/R) titles differ across services?"
    )
    df = queries.fetch_maturity_mix()
    if df.empty:
        st.warning("No maturity breakdown data is available.")
        return

    services = sorted(df["service_name"].unique())
    selected = st.multiselect(
        "Services to compare",
        services,
        default=services,
        key="q8_services",
    )
    if not selected:
        st.info("Select at least one service to contrast maturity mix.")
        return

    filtered = df[df["service_name"].isin(selected)].copy()
    if filtered.empty:
        st.info("No records for the selected services.")
        return

    fig = px.bar(
        filtered,
        x="service_name",
        y="title_count",
        color="content_group",
        # barnorm="percent",
        labels={
            "service_name": "Platform",
            "title_count": "Catalog share (count)",
            "content_group": "Content grouping",
        },
        title="Family vs. mature mixes",
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("SQL query"):
        st.code(Q8_SQL, language="sql")

    with st.expander("Answer / interpretation"):
        st.markdown(_summarize_q8(filtered))
def _format_int(value: float | int) -> str:
    return f"{int(value):,}"


def _format_pct(value: float) -> str:
    if pd.isna(value):
        return "0%"
    return f"{value:.1%}"


def _summarize_q1(df: pd.DataFrame) -> str:
    if df.empty:
        return "No services selected."
    if len(df) == 1:
        row = df.iloc[0]
        return f"{row['service_name']} currently offers {_format_int(row['total_titles'])} titles."
    leader = df.loc[df["total_titles"].idxmax()]
    trailer = df.loc[df["total_titles"].idxmin()]
    diff = leader["total_titles"] - trailer["total_titles"]
    return (
        f"{leader['service_name']} leads with {_format_int(leader['total_titles'])} titles, "
        f"{_format_int(diff)} more than {trailer['service_name']}."
    )


def _summarize_q2(df: pd.DataFrame) -> str:
    if df.empty:
        return "No services selected."
    ratios = df.copy()
    ratios["total"] = ratios["movie_count"] + ratios["tv_show_count"]
    ratios["movie_share"] = ratios["movie_count"] / ratios["total"].where(ratios["total"] != 0, pd.NA)
    ratios["movie_share"] = ratios["movie_share"].fillna(0)

    movie_heavy = ratios.loc[ratios["movie_share"].idxmax()]
    tv_heavy = ratios.loc[ratios["movie_share"].idxmin()]

    tv_share = 1 - movie_heavy["movie_share"]
    most_tv_share = 1 - tv_heavy["movie_share"]

    if len(ratios) == 1:
        return (
            f"{movie_heavy['service_name']} splits its catalog "
            f"{_format_pct(movie_heavy['movie_share'])} movies vs {_format_pct(tv_share)} TV."
        )

    return (
        f"{movie_heavy['service_name']} is the most movie-forward catalog "
        f"({_format_pct(movie_heavy['movie_share'])} movies), while {tv_heavy['service_name']} "
        f"leans toward series with {_format_pct(most_tv_share)} TV shows."
    )


def _summarize_q3(df: pd.DataFrame) -> str:
    if df.empty:
        return "No services selected."
    leader = df.loc[df["country_count"].idxmax()]
    trailer = df.loc[df["country_count"].idxmin()]
    if len(df) == 1:
        return f"{leader['service_name']} includes titles from {_format_int(leader['country_count'])} countries."
    diff = leader["country_count"] - trailer["country_count"]
    return (
        f"{leader['service_name']} spans {_format_int(leader['country_count'])} countries, "
        f"{_format_int(diff)} more than {trailer['service_name']}."
    )


def _summarize_q4(df: pd.DataFrame) -> str:
    if df.empty:
        return "No countries selected."
    top = df.head(min(3, len(df)))
    listing = ", ".join(
        f"{row['country_name']} ({_format_int(row['title_count'])})" for _, row in top.iterrows()
    )
    return f"Top contributors: {listing}."


def _summarize_q5(df: pd.DataFrame) -> str:
    if df.empty:
        return "No genres selected."
    top = df.head(min(3, len(df)))
    listing = ", ".join(
        f"{row['genre_name']} ({_format_int(row['title_count'])})" for _, row in top.iterrows()
    )
    return f"Most common genres: {listing}."


def _summarize_q6(df: pd.DataFrame, threshold: float) -> str:
    if df.empty:
        return f"No genre/service pairs exceed the {_format_pct(threshold)} threshold."
    row = df.iloc[0]
    return (
        f"{row['service_name']} controls {_format_pct(row['service_share'])} of all {row['genre_name']} titles "
        "within the dataset, making it the clearest near-exclusive pairing in view."
    )


def _summarize_q7(df: pd.DataFrame) -> str:
    if df.empty:
        return "No services selected."
    lines = []
    for service, group in df.groupby("service_name"):
        dominant = group.loc[group["share"].idxmax()]
        lines.append(f"- **{service}**: {dominant['rating_bucket']} leads at {_format_pct(dominant['share'])}.")
    return "\n".join(lines)


def _summarize_q8(df: pd.DataFrame) -> str:
    if df.empty:
        return "No services selected."
    df = df.copy()
    df["share"] = df.groupby("service_name")["title_count"].transform(lambda s: s / s.sum())
    lines = []
    for service, group in df.groupby("service_name"):
        family_share = group.loc[group["content_group"] == "Family (G/PG)", "share"].sum()
        mature_share = group.loc[group["content_group"] == "Mature (PG-13+/R)", "share"].sum()
        leaning = "family-leaning" if family_share >= mature_share else "mature-leaning"
        lines.append(
            f"- **{service}**: family {_format_pct(family_share)} vs mature {_format_pct(mature_share)} ({leaning})."
        )
    return "\n".join(lines)
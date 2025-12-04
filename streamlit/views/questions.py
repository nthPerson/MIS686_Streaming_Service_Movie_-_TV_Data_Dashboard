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
    CASE
        WHEN g.genre_name IN (
            'Children & Family Movies','Family','Kids','Teen',
            'Teen TV Shows','Young Adult Audience','Coming of Age'
        ) THEN 'Kids & Family'

        WHEN g.genre_name IN (
            'Comedy','Comedies','TV Comedies','Sitcom',
            'Stand Up','Stand-Up Comedy','Stand-Up Comedy & Talk Shows',
            'Sketch Comedy','Parody','Variety','Late Night',
            'Talk Show','Talk Show and Variety',
            'Game Shows','Game Show / Competition','Buddy'
        ) THEN 'Comedy'

        WHEN g.genre_name IN (
            'Drama','Dramas','TV Dramas','Anthology',
            'Soap Opera / Melodrama','Medical'
        ) THEN 'Drama'

        WHEN g.genre_name IN (
            'Action','Action & Adventure','Action-Adventure','Adventure',
            'Disaster','Spy/Espionage','Police/Cop','Survival',
            'Superhero','Military and War','Western','TV Action & Adventure'
        ) THEN 'Action & Adventure'

        WHEN g.genre_name IN (
            'Horror','Horror Movies','Thriller','Thrillers','Suspense',
            'TV Horror','TV Thrillers'
        ) THEN 'Horror & Thriller'

        WHEN g.genre_name IN (
            'Romance','Romantic Movies','Romantic TV Shows','Romantic Comedy'
        ) THEN 'Romance'

        WHEN g.genre_name IN (
            'Sci-Fi & Fantasy','Science Fiction','TV Sci-Fi & Fantasy','Fantasy'
        ) THEN 'Sci-Fi & Fantasy'

        WHEN g.genre_name IN (
            'Crime','Crime TV Shows','Mystery','TV Mysteries'
        ) THEN 'Crime & Mystery'

        WHEN g.genre_name IN (
            'Documentary','Documentaries','Docuseries','Biographical',
            'Historical','History','Science & Nature TV',
            'Science & Technology','Animals & Nature','Special Interest','News'
        ) THEN 'Documentary & History'

        WHEN g.genre_name IN (
            'Music','Music & Musicals','Music Videos and Concerts',
            'Musical','Concert Film','Dance','Arts'
        ) THEN 'Music & Performing Arts'

        WHEN g.genre_name IN (
            'Anime','Anime Features','Anime Series','Animation','Adult Animation','Cartoons'
        ) THEN 'Animation & Anime'

        WHEN g.genre_name IN (
            'International','International Movies','International TV Shows',
            'British TV Shows','Korean TV Shows','Spanish-Language TV Shows',
            'Latino','Black Stories'
        ) THEN 'International / Regional'

        ELSE 'Other'
    END AS genre_category,
    COUNT(DISTINCT tg.title_id) AS title_count
FROM genre g
JOIN title_genre tg
    ON g.genre_id = tg.genre_id
JOIN streaming_availability sa
    ON sa.title_id = tg.title_id
GROUP BY
    CASE
        WHEN g.genre_name IN (
            'Children & Family Movies','Family','Kids','Teen',
            'Teen TV Shows','Young Adult Audience','Coming of Age'
        ) THEN 'Kids & Family'

        WHEN g.genre_name IN (
            'Comedy','Comedies','TV Comedies','Sitcom',
            'Stand Up','Stand-Up Comedy','Stand-Up Comedy & Talk Shows',
            'Sketch Comedy','Parody','Variety','Late Night',
            'Talk Show','Talk Show and Variety',
            'Game Shows','Game Show / Competition','Buddy'
        ) THEN 'Comedy'

        WHEN g.genre_name IN (
            'Drama','Dramas','TV Dramas','Anthology',
            'Soap Opera / Melodrama','Medical'
        ) THEN 'Drama'

        WHEN g.genre_name IN (
            'Action','Action & Adventure','Action-Adventure','Adventure',
            'Disaster','Spy/Espionage','Police/Cop','Survival',
            'Superhero','Military and War','Western','TV Action & Adventure'
        ) THEN 'Action & Adventure'

        WHEN g.genre_name IN (
            'Horror','Horror Movies','Thriller','Thrillers','Suspense',
            'TV Horror','TV Thrillers'
        ) THEN 'Horror & Thriller'

        WHEN g.genre_name IN (
            'Romance','Romantic Movies','Romantic TV Shows','Romantic Comedy'
        ) THEN 'Romance'

        WHEN g.genre_name IN (
            'Sci-Fi & Fantasy','Science Fiction','TV Sci-Fi & Fantasy','Fantasy'
        ) THEN 'Sci-Fi & Fantasy'

        WHEN g.genre_name IN (
            'Crime','Crime TV Shows','Mystery','TV Mysteries'
        ) THEN 'Crime & Mystery'

        WHEN g.genre_name IN (
            'Documentary','Documentaries','Docuseries','Biographical',
            'Historical','History','Science & Nature TV',
            'Science & Technology','Animals & Nature','Special Interest','News'
        ) THEN 'Documentary & History'

        WHEN g.genre_name IN (
            'Music','Music & Musicals','Music Videos and Concerts',
            'Musical','Concert Film','Dance','Arts'
        ) THEN 'Music & Performing Arts'

        WHEN g.genre_name IN (
            'Anime','Anime Features','Anime Series','Animation','Adult Animation','Cartoons'
        ) THEN 'Animation & Anime'

        WHEN g.genre_name IN (
            'International','International Movies','International TV Shows',
            'British TV Shows','Korean TV Shows','Spanish-Language TV Shows',
            'Latino','Black Stories'
        ) THEN 'International / Regional'

        ELSE 'Other'
    END
ORDER BY title_count DESC;
"""

Q6_SQL = """
WITH genre_mapped AS (
    SELECT
        sa.streaming_service_id,
        sa.title_id,
        CASE
            WHEN g.genre_name IN (
                'Children & Family Movies','Family','Kids','Teen',
                'Teen TV Shows','Young Adult Audience','Coming of Age'
            ) THEN 'Kids & Family'

            WHEN g.genre_name IN (
                'Comedy','Comedies','TV Comedies','Sitcom',
                'Stand Up','Stand-Up Comedy','Stand-Up Comedy & Talk Shows',
                'Sketch Comedy','Parody','Variety','Late Night',
                'Talk Show','Talk Show and Variety',
                'Game Shows','Game Show / Competition','Buddy'
            ) THEN 'Comedy'

            WHEN g.genre_name IN (
                'Drama','Dramas','TV Dramas','Anthology',
                'Soap Opera / Melodrama','Medical'
            ) THEN 'Drama'

            WHEN g.genre_name IN (
                'Action','Action & Adventure','Action-Adventure','Adventure',
                'Disaster','Spy/Espionage','Police/Cop','Survival',
                'Superhero','Military and War','Western','TV Action & Adventure'
            ) THEN 'Action & Adventure'

            WHEN g.genre_name IN (
                'Horror','Horror Movies','Thriller','Thrillers','Suspense',
                'TV Horror','TV Thrillers'
            ) THEN 'Horror & Thriller'

            WHEN g.genre_name IN (
                'Romance','Romantic Movies','Romantic TV Shows','Romantic Comedy'
            ) THEN 'Romance'

            WHEN g.genre_name IN (
                'Sci-Fi & Fantasy','Science Fiction','TV Sci-Fi & Fantasy','Fantasy'
            ) THEN 'Sci-Fi & Fantasy'

            WHEN g.genre_name IN (
                'Crime','Crime TV Shows','Mystery','TV Mysteries'
            ) THEN 'Crime & Mystery'

            WHEN g.genre_name IN (
                'Documentary','Documentaries','Docuseries','Biographical',
                'Historical','History','Science & Nature TV',
                'Science & Technology','Animals & Nature','Special Interest','News'
            ) THEN 'Documentary & History'

            WHEN g.genre_name IN (
                'Music','Music & Musicals','Music Videos and Concerts',
                'Musical','Concert Film','Dance','Arts'
            ) THEN 'Music & Performing Arts'

            WHEN g.genre_name IN (
                'Anime','Anime Features','Anime Series','Animation',
                'Adult Animation','Cartoons'
            ) THEN 'Animation & Anime'

            WHEN g.genre_name IN (
                'International','International Movies','International TV Shows',
                'British TV Shows','Korean TV Shows','Spanish-Language TV Shows',
                'Latino','Black Stories'
            ) THEN 'International / Regional'

            ELSE 'Other'
        END AS genre_category
    FROM streaming_availability sa
    JOIN title_genre tg
        ON sa.title_id = tg.title_id
    JOIN genre g
        ON tg.genre_id = g.genre_id
),

genre_service_counts AS (
    SELECT
        s.service_name,
        gm.genre_category,
        COUNT(DISTINCT gm.title_id) AS title_count
    FROM genre_mapped gm
    JOIN streaming_service s
        ON gm.streaming_service_id = s.streaming_service_id
    GROUP BY
        s.service_name,
        gm.genre_category
),

genre_totals AS (
    SELECT
        genre_category,
        SUM(title_count) AS genre_total_titles
    FROM genre_service_counts
    GROUP BY
        genre_category
),

service_totals AS (
    SELECT
        service_name,
        SUM(title_count) AS service_total_titles
    FROM genre_service_counts
    GROUP BY
        service_name
),

with_shares AS (
    SELECT
        gsc.service_name,
        gsc.genre_category,
        gsc.title_count,
        gt.genre_total_titles,
        st.service_total_titles,

        gsc.title_count * 1.0 / gt.genre_total_titles AS dominance_share,

        gsc.title_count * 1.0 / st.service_total_titles AS service_share
    FROM genre_service_counts gsc
    JOIN genre_totals gt
        ON gsc.genre_category = gt.genre_category
    JOIN service_totals st
        ON gsc.service_name = st.service_name
),

ranked AS (
    SELECT
        service_name,
        genre_category,
        title_count,
        genre_total_titles,
        service_total_titles,
        dominance_share,
        service_share,
        ROW_NUMBER() OVER (
            PARTITION BY service_name
            ORDER BY dominance_share DESC
        ) AS rn
    FROM with_shares
)

SELECT
    service_name,
    genre_category,
    title_count,
    ROUND(dominance_share * 100, 1) AS dominance_share_pct,
    ROUND(service_share * 100, 1)   AS service_share_pct
FROM ranked
WHERE rn <= 5   
ORDER BY
    service_name,
    dominance_share_pct DESC;

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

Q1_TEXT = """
Amazon Prime Video offers the most extensive catalog in this sample, with 9,660 distinct titles, followed closely by Netflix with 8,798 titles. In contrast, Hulu provides a more moderate library of 3,072 titles, while Disney+ has the smallest catalog, with 1,450 titles.

These quantitative differences align with the strategic positioning of each platform during the dataset period. Amazon Prime Video and Netflix pursue a broad, high-variety content strategy, emphasizing extensive libraries that can serve a wide range of tastes and viewing occasions. Their large catalogs support a value proposition built on depth and variety, enabling them to attract heterogeneous audience segments and encourage longer viewing time through abundant choice.

Hulu's mid-sized catalog suggests an intermediate positioning: although it offers substantially fewer titles than Amazon Prime Video and Netflix, its library is still extensive enough to compete meaningfully, particularly in TV series and current-season content. Finally, Disney+'s relatively small catalog aligns with a focused, curated strategy built on a strong portfolio of proprietary franchises (e.g., Disney Animation, Pixar, Marvel, Star Wars, and National Geographic). Instead of competing on sheer volume, Disney+ competes on the strength, recognizability, and brand equity of its intellectual property.

"""

Q2_TEXT = """
For Amazon Prime Video, approximately 80.8% of titles are classified as movies (7,801 out of 9,660), while 19.2% are classified as TV shows (1,853 out of 9,660). The number of titles tagged as both movie and TV show is negligible (6 titles, well under 1% of the catalog). This translates into a movie-to-TV ratio of about 4.2 to 1, indicating that Amazon's catalog in this dataset is strongly skewed toward films. Such a composition is consistent with a strategy that emphasizes breadth and variety in movie content, including long-tail and catalog titles, as a primary source of perceived value.

Disney+ also features a movie-dominant catalog, but with somewhat lower skew. In this dataset, about 72.4% of its titles are movies (1,050 out of 1,450) and 27.4% are TV shows (397 out of 1,450), with only three titles classified as both. The implied movie-to-TV ratio is roughly 2.6 to 1. This pattern aligns well with Disney+'s known positioning as a platform built around high-value, proprietary intellectual property—Disney Animation, Pixar, Marvel, Star Wars, and related brands—where feature films serve as flagship assets and television series primarily extend and deepen existing franchises rather than maximize sheer volume.

Hulu, by contrast, presents a markedly different profile. In the database, 1,483 titles are classified as movies and 1,585 as TV shows, out of a total of 3,072 titles. This corresponds to roughly 48.3% movies and 51.6% TV shows, with only four titles in the overlapping category. The resulting movie-to-TV ratio is about 0.94 to 1, meaning that TV shows slightly outnumber movies. This near-balanced but TV-leaning mix is consistent with a strategic emphasis on episodic content and current-season or catch-up television, supporting patterns of habitual, ongoing viewing rather than predominantly one-off film consumption.

Netflix occupies an intermediate position between the strongly movie-dominant services and Hulu's more TV-heavy profile. In this snapshot, 6,123 titles are movies, and 2,670 are TV shows, out of 8,799 total titles. That implies approximately 69.6% movies and 30.3% TV shows, with six titles classified as both. The movie-to-TV ratio is therefore about 2.3:1. This composition reflects a hybrid strategy: Netflix maintains an extensive film library to provide breadth and variety across genres and regions, while simultaneously investing heavily in TV series, which play a central role in sustaining engagement and subscription retention through binge-watching and serialized storytelling.

"""

Q3_TEXT = """
Netflix has the widest geographic coverage, with titles produced in 122 different countries. Hulu follows with content from 57 countries, indicating a moderately diverse but more regionally concentrated catalog. Amazon Prime Video includes titles from 50 countries, reflecting a slightly narrower international spread than Hulu. Disney+ has the smallest geographic footprint in this comparison, with productions originating from 47 countries. Overall, Netflix clearly leads in global country coverage, while Hulu, Amazon Prime Video, and Disney+ draw from roughly half or fewer of the production countries represented in Netflix's library.
"""

Q4_TEXT = """
Across all four streaming services combined, the largest contributors of titles are:

United States - by far the dominant source, with 6,226 titles.

India - close behind, with 1,290 titles.

United Kingdom - the third-largest contributor with 1,163 titles.

Canada - contributing 640 titles.

Japan - providing 591 titles.

After these, countries such as France, Germany, South Korea, Spain, Australia, Mexico, China, Egypt, Italy, and Turkey each contribute smaller but still meaningful numbers of titles (generally below 500 each). Overall, the catalog is heavily dominated by U.S. productions, with the U.K. and India forming a clear second tier of content sources.

"""

Q5_TEXT = """
To answer the question about the most common genres overall, we first grouped individual genre labels that described the same underlying concept. For example, labels such as Drama, Dramas, TV Dramas, and related sub-types were combined into a single Drama category; similarly, various comedy labels (e.g., Comedy, Comedies, TV Comedies, Sitcom, Stand-Up Comedy), different documentary and history labels, and multiple children, horror, action, and international tags were consolidated into broader, analytically meaningful genre families. This allowed us to avoid double-counting very similar categories and to get a clearer view of audience-relevant content clusters.

After this consolidation, Drama emerges as the dominant genre family with 7,828 titles, followed by Comedy with 5,871 titles. Together, these two narrative pillars account for a very large share of the catalog and confirm that emotionally driven stories and humor form the core of streaming content supply. The third-largest category is International / Regional content with 5,011 titles, highlighting the significant weight of non-U.S. and region-specific stories and indicating that global and multicultural programming is now a central part of the overall offering rather than a niche.
"""

Q6_TEXT = """
To identify genres that are most unique to each platform, we first consolidated detailed genre labels from the database (for example, TV Dramas, Dramas, Romantic Movies, Anime Series, International TV Shows, etc.) into broader genre families such as Drama, Comedy, Kids & Family, Horror & Thriller, International / Regional, and others. Using these consolidated categories, we then examined which genres each service carries in especially large numbers compared with competitors.

For Amazon Prime Video, the most distinctive genres are Drama with 3,710 titles, Horror & Thriller with 2,048 titles, Action & Adventure with 1,944 titles, and Documentary & History with 1,627 titles, alongside Music & Performing Arts with 634 titles. This pattern highlights Amazon's relative strength in intense narrative content, large-scale action, and factual or historically oriented programming, plus a notable emphasis on music and performance.

Disney+ stands out most clearly in family and animation content. It has 919 titles in Kids & Family and 542 in Animation & Anime, followed by Action & Adventure with 470 titles, Documentary & History with 381, and Sci-Fi & Fantasy with 278. These figures reinforce Disney+'s positioning as a family-centric platform built around animated titles and franchise properties such as Disney, Pixar, Marvel, and Star Wars.

For Hulu, the top genres are Documentary & History (664 titles), Action & Adventure (646), Other (602), Animation & Anime (400), and Crime & Mystery (276). This mix suggests a distinctive profile focused on factual content, crime and investigative stories, and a diverse set of TV-style and niche categories captured under “Other.”

Netflix is most strongly differentiated by its International / Regional catalog, with 4,272 titles, far exceeding any other platform in this category. In addition, it has 2,628 titles in Comedy, 2,088 in Other, 1,002 in Romance, and 558 in Crime & Mystery. These numbers underscore Netflix's role as the most global platform, with extensive international content, and a strong emphasis on comedy, romance, and varied serialized storytelling.

"""

_Q6_METRIC_LABELS = {
    "dominance_share_pct": "Dominance share (% of all titles tagged with that genre)",
    "service_share_pct": "Service share (% of that service's catalog)",
}

Q7_TEXT = """
The original rating codes were first normalized into five categories—G, PG, PG-13, R/TV-MA, and Unrated/Other and then counted by platform using the query provided.

The results show clear positioning differences. Disney+ is the most family-oriented: it has 621 G and 681 PG titles, compared with only 145 PG-13, 0 R/TV-MA, and just 3 Unrated/Other, so almost all of its catalog is explicitly suitable for children and families. Netflix, by contrast, is strongly maturity-skewed, with 574 G and 1,481 PG titles but far larger counts in PG-13 (2,611) and especially R/TV-MA (3,942), indicating a catalog focused on teen and adult viewing with some family content on the side. Hulu sits between these extremes: it offers 199 G and 471 PG titles, but also 845 PG-13 and 737 R/TV-MA, plus 820 Unrated/Other, suggesting a mix of family, teen, and mature content with a noticeable adult tilt. Amazon Prime Video has substantial numbers in every rated band (G=1,515; PG=461; PG-13=601; R/TV-MA=1,095) but is dominated by Unrated/Other (5,988), meaning that while it clearly carries both family and mature titles, incomplete rating data make its overall maturity profile less transparent than the others.
"""

Q8_TEXT = """
To compare the content maturity profiles of the four streaming services, maturity ratings were first normalized into four bands—G, PG, PG-13, and R/TV-MA—and then grouped into two broader categories: family-friendly content (G and PG) and mature content (PG-13 and R/TV-MA). The query then calculated, for each service, how many titles fall into each group and what share they represent of all titles with a valid maturity rating.

The results show a clear gradient from strongly family-oriented to strongly mature-oriented platforms. Disney+ is the most family-centric service by a wide margin. Out of 1,447 classified titles, 1,302 are family-friendly, meaning 90.0% of its catalog in this subset is rated G/PG, and only 10.0% (145 titles) falls into the PG-13/R-TV-MA bucket. This profile is consistent with Disney+'s positioning as a platform for children, families, and all-ages franchise content.

Amazon Prime Video presents a more balanced but still slightly family-leaning mix. Among 3,672 classified titles, 1,976 (53.8%) are family-friendly and 1,696 (46.2%) are mature. This near 50-50 split suggests that Amazon serves both households seeking lighter, all-ages content and viewers interested in more intense or adult-oriented programming, without a strong tilt to either extreme.

By contrast, Hulu and Netflix are clearly maturity-skewed. Hulu has 2,252 classified titles, of which only 670 (29.8%) are G/PG, while 1,582 (70.2%) are PG-13 or R/TV-MA. Netflix is even more strongly weighted toward mature content: out of 8,608 classified titles, 2,055 (just 23.9%) are family-friendly, whereas 6,553 (a dominant 76.1%) fall into the mature category. These figures indicate that both services primarily target teen and adult audiences, with Netflix in particular emphasizing more mature viewing while still maintaining a sizeable—but clearly secondary—family-friendly segment.
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
    table_df = filtered.rename(
        columns={
            "service_name": "Service",
            "total_titles": "Titles",
            "movie_count": "Movies",
            "tv_show_count": "TV Shows",
        }
    )
    desired_columns = ["Service", "Titles", "Movies", "TV Shows"]
    table_df = table_df[[col for col in desired_columns if col in table_df.columns]]

    st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
    )

    with st.expander("SQL query"):
        st.code(Q1_SQL, language="sql")

    with st.expander("Answer / interpretation"):
        st.markdown("## Dynamic Answer (changes with choice of filter):")
        st.markdown(_summarize_q1(filtered))
        st.markdown(f"## Static Analysis:\n{Q1_TEXT}")



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
        st.markdown("## Dynamic Answer (changes with choice of filter):")
        st.markdown(_summarize_q2(filtered))
        st.markdown(f"## Static Analysis:\n{Q2_TEXT}")


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
        st.markdown("## Dynamic Answer (changes with choice of filter):")
        st.markdown(_summarize_q3(filtered))
        st.markdown(f"## Static Analysis:\n{Q3_TEXT}")


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
        st.markdown("## Dynamic Answer (displays top 3):")
        st.markdown(_summarize_q4(filtered))
        st.markdown(f"## Static Analysis:\n{Q4_TEXT}")



def _render_q5() -> None:
    st.header("Q5. What are the most common genres overall?")
    df = queries.fetch_genre_distribution(None)
    if df.empty:
        st.warning("No genre information is available.")
        return

    genre_totals = df.sort_values("title_count", ascending=False)

    top_n = st.slider("Top genres to highlight", min_value=5, max_value=12, value=10, key="q5_top")
    filtered = genre_totals.head(top_n)

    fig = px.bar(
        filtered,
        x="genre_category",
        y="title_count",
        text_auto=".0f",
        labels={"genre_category": "Genre", "title_count": "Titles"},
        title=f"Top {top_n} genres across all services",
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("SQL query"):
        st.code(Q5_SQL, language="sql")

    with st.expander("Answer / interpretation"):
        st.markdown("## Dynamic Answer (displays top 3):")
        st.markdown(_summarize_q5(filtered))
        st.markdown(f"## Static Analysis:\n{Q5_TEXT}")


def _render_q6() -> None:
    st.header("Q6. Which genres are most unique or exclusive to individual platforms?")
    df = queries.fetch_genre_uniqueness()
    if df.empty:
        st.warning("No genre uniqueness data is available.")
        return

    services = sorted(df["service_name"].unique())
    selected = st.multiselect(
        "Services to highlight",
        services,
        default=services,
        key="q6_services",
    )
    if not selected:
        st.info("Select at least one service to evaluate distinctive genres.")
        return

    filtered = df[df["service_name"].isin(selected)].copy()

    top_n = st.slider(
        "Top ranked genres per service",
        min_value=1,
        max_value=5,
        value=5,
        key="q6_top",
    )
    filtered = filtered[filtered["rn"] <= top_n]

    metric = st.selectbox(
        "Share metric to visualize",
        options=list(_Q6_METRIC_LABELS.keys()),
        format_func=lambda key: _Q6_METRIC_LABELS[key],
        key="q6_metric",
    )

    if filtered.empty:
        st.info("No records match the selected services and rank cutoff.")
        return

    filtered = filtered.sort_values(["service_name", metric], ascending=[True, False])

    fig = px.bar(
        filtered,
        x=metric,
        y="genre_category",
        color="service_name",
        orientation="h",
        text_auto=".1f",
        labels={
            "genre_category": "Genre",
            "service_name": "Platform",
            metric: _Q6_METRIC_LABELS[metric],
        },
        hover_data={
            "title_count": True,
            "dominance_share_pct": True,
            "service_share_pct": True,
            "rn": False,
        },
        title="Top genre differentiators per service",
    )
    fig.update_layout(xaxis=dict(ticksuffix="%"))
    st.plotly_chart(fig, use_container_width=True)

    table_df = (
        filtered.rename(
            columns={
                "service_name": "Service",
                "genre_category": "Genre",
                "title_count": "Titles",
                "dominance_share_pct": "Dominance (%)",
                "service_share_pct": "Service Share (%)",
                "rn": "Rank",
            }
        )
        .sort_values(["Service", "Rank"])
    )
    st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
    )

    with st.expander("SQL query"):
        st.code(Q6_SQL, language="sql")

    with st.expander("Answer / interpretation"):
        st.markdown("## Dynamic Answer (shows per-service standouts):")
        st.markdown(_summarize_q6(filtered, metric))
        st.markdown(f"## Static Analysis:\n{Q6_TEXT}")


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
        st.markdown("## Dynamic Answer (changes with choice of filter):")
        st.markdown(_summarize_q7(filtered))
        st.markdown(f"## Static Analysis:\n{Q7_TEXT}")



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
        st.markdown("## Dynamic Answer (changes with choice of filter):")
        st.markdown(_summarize_q8(filtered))
        st.markdown(f"## Static Analysis:\n{Q8_TEXT}")


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
        f"{row.get('genre_category', row.get('genre_name'))} ({_format_int(row['title_count'])})"
        for _, row in top.iterrows()
    )
    return f"Most common genres: {listing}."


def _summarize_q6(df: pd.DataFrame, metric: str) -> str:
    if df.empty:
        return "No standout genre/service combinations for the current selection."

    row = df.iloc[0]
    other_metric = "service_share_pct" if metric == "dominance_share_pct" else "dominance_share_pct"

    metric_text = _Q6_METRIC_LABELS.get(metric, "Selected share").split(" (")[0].lower()
    other_text = _Q6_METRIC_LABELS.get(other_metric, "Secondary share").split(" (")[0].lower()

    metric_value = "0.0%" if pd.isna(row.get(metric)) else f"{row[metric]:.1f}%"
    other_value = "0.0%" if pd.isna(row.get(other_metric)) else f"{row[other_metric]:.1f}%"

    return (
        f"{row['service_name']} leads the {row['genre_category']} category with {metric_value} {metric_text}. "
        f"That genre also represents {other_value} of its catalog by {other_text}."
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
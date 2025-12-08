# Application Overview

The dashboard analyzes combined catalogs from Netflix, Amazon Prime Video, Hulu, and Disney+. It answers eight analytical questions on catalog size, mix, geography, genre concentration, and maturity ratings using interactive charts and tables.

## What the app provides
- **Eight question-driven visuals** (home page): platform totals; movie vs TV mix; country breadth; top countries by title count; genre buckets; genre dominance per service; age-rating mix; family vs mature grouping (see `streamlit/views/questions.py`).
- **Shared filters and KPIs**: sidebar controls and `FilterState` flow through `streamlit/filters.py` and `streamlit/queries.py`, keeping all charts consistent.
- **Role-aware pages**: Viewer, Analyst, and Admin experiences are gated in `streamlit/app.py` with dedicated views (`viewer_dashboard.py`, `analyst_dashboard.py`, `admin_dashboard.py`).
- **Additional sections**: overview KPIs and platform breakdown (`views/overview.py`), high-level analytics (`views/high_level.py`), trends, recommendations, distribution, and catalog browsing within `streamlit/views/`.
- **Transparent SQL**: question cards expose the underlying queries and interpretations alongside each visualization.

## Data foundation
- Normalized MySQL schema defined in `documents/database/DATABASE_SCHEMA.md` and DDLs (`documents/tv_movie_DDL.sql`).
- ETL pipeline (`data_wrangling/etl_streaming_titles.py`) loads the four CSV catalogs into core tables (titles, genres, countries, people/roles, streaming availability).
- Central query layer in `streamlit/queries.py` supplies all views; `streamlit/db.py` handles pooled connections for pandas DataFrames.

## User experience at a glance
- Home: eight analytical questions with interactive filters and SQL/answer expanders.
- High-Level analytics: aggregated KPIs and charts without role restrictions.
- Viewer/Analyst/Admin dashboards: tailored navigation and controls per role, surfaced through the sidebar and maintained in session state.

For setup and ETL instructions, see `APP_SETUP_README.md`. To launch the app locally, run `streamlit run streamlit/app.py` after configuration.

# Streaming Dashboard Scaffold

This document explains how the new Streamlit dashboard package is organized and how to run it locally. Refer to `README.md` for overall project context.

## Architecture

```
streamlit/
├── app.py                # Entry point wiring settings, sidebar filters, and sections
├── config.py             # `.env` driven settings using dataclasses and cached loader
├── db.py                 # MySQL connection pool helpers returning pandas DataFrames
├── filters.py            # Sidebar widgets + filter state dataclasses
├── queries.py            # Parameterized SQL builders shared across sections
└── views/
    ├── overview.py       # KPI cards + Plotly bar chart
    ├── distribution.py   # Genre/country Matplotlib visuals
    ├── trends.py         # Plotly line charts for release & addition trends
    ├── recommendations.py# Genre-overlap similarity finder
    └── catalog.py        # Filtered titles table
```

Key characteristics:
- Modular layout avoids a monolithic `app.py`; each section encapsulates its visuals.
- Both Plotly and Matplotlib are used (`views/overview.py`, `views/trends.py` vs `views/distribution.py`).
- All queries live in `queries.py`, ensuring consistent filtering logic.
- Configuration pulls from `.env` and can be reused for future AWS RDS hosting.

## Prerequisites

1. **Python environment**: create/activate a virtualenv, then install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. **Database**: run the ETL script against your local MySQL instance so the `streaming_media_db` schema is populated:
   ```bash
   python data_wrangling/etl_streaming_titles.py
   ```
3. **Environment variables**: create a `.env` file (or export variables) with:
   ```
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=your_user
   DB_PASSWORD=your_password
   DB_NAME=streaming_media_db
   STREAMLIT_TITLE=Streaming Media Intelligence Dashboard
   ```

## Running the Dashboard

From the repo root:

```bash
streamlit run streamlit/app.py
```

The app loads sidebar filter metadata from the database, then renders the following sections:
1. **Overview** – high-level KPIs and a Plotly stacked bar comparing platform mixes.
2. **Distribution** – Matplotlib charts of genre and country concentrations.
3. **Trends** – Plotly line charts for release-year momentum and platform additions.
4. **Recommendations** – simple shared-genre similarity explorer.
5. **Catalog** – filterable table for detailed inspection.

If database credentials are incorrect or metadata fails to load, the sidebar displays the exception so you can adjust settings quickly.

## Extending

- Add new visual sections in `streamlit/views/` and register them in `streamlit/app.py`.
- Centralize any additional SQL helpers inside `streamlit/queries.py` for consistent filtering.
- When preparing for AWS RDS, update `.env` with the hosted connection string—no code changes required.

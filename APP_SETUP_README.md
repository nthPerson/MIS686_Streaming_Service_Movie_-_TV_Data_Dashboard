# Setup and Data Loading Guide

Follow these steps to configure the environment, database, and ETL pipeline.

## 1) Prerequisites
- Python 3.9+ (3.10 recommended)
- MySQL 8.0.4 (or compatible) with client access
- A terminal to run ETL commands and launch the app

## 2) Python environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3) Database creation
Run the DDL located at the path below in MySQL Workbench to create the `streaming_media_db` schema and tables:
```
# SQL DDL script (run in MySQL Workbench to create database)
documents/database/monolith_hosting_DDL.sql
```

## 4) Environment variables
Create `.env` (copy from `.env.example`) with your connection details:
```
DB_HOST=localhost
DB_PORT=3306
DB_USER=replace_with_your_database_username
DB_PASSWORD=replace_with_your_password
DB_NAME=streaming_media_db
```

## 5) ETL: load the CSV catalogs
Change to the ETL directory first to avoid CWD issues, then run the desired mode:
```bash
cd data_wrangling  # run all of the following commands from the data_wrangling/ directory
python etl_streaming_titles.py --test-connection   # verify tables & connectivity
python etl_streaming_titles.py --dry-run           # simulate inserts, show samples
python etl_streaming_titles.py --live-run          # load data (default if no flag)
```
The script reads the four CSVs in `raw_data/` and populates all core tables (titles, genres, countries, people/roles, streaming availability). See the ETL logic in `data_wrangling/etl_streaming_titles.py`.

## 6) Verify load
In MySQL:
```sql
USE streaming_media_db;
SELECT COUNT(*) FROM title;
SELECT service_name, COUNT(*) AS titles
FROM streaming_service s
JOIN streaming_availability a ON a.streaming_service_id = s.streaming_service_id
GROUP BY service_name;
```

## 7) Run the app
```bash
streamlit run streamlit/app.py
```

If you change DB credentials, update `.env` and rerun `--test-connection`. Re-run the live ETL when raw CSVs are updated.

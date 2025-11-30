"""
ETL script for loading Netflix / Prime / Hulu / Disney+ CSV catalogs
into the normalized MySQL schema.

Tables expected (already created via your DDL):
- rating
- streaming_service
- title
- movie
- tv_show
- genre
- title_genre
- country
- title_country
- person
- role_type
- title_person_role
- streaming_availability
"""

import pymysql
from pymysql import err as pymysql_err
import pandas as pd
import re
import argparse
import sys
from datetime import datetime
import os

# Load environment variables from /.env/
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '../', '.env'))

# ===============================
# 1. DB CONNECTION CONFIG
# ===============================

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),  # Default to 'localhost' if not set
    "port": int(os.getenv("DB_PORT", 3306)),    # Default to 3306 if not set
    "user": os.getenv("DB_USER", "root"),  # Default to 'movie_tv_db_user' if not set
    "password": os.getenv("DB_PASSWORD", "password"),  # Default to 'movie_tv_db_user_password' if not set
    "database": os.getenv("DB_NAME", "streaming_media_db")  # Default to 'streaming_media_db' if not set
}

# ===============================
# 1b. LENGTH CONSTRAINTS (from DDL)
# ===============================

MAX_LENGTHS = {
    "rating_code": 10,
    "service_name": 100,
    "country_of_operation": 100,
    "url": 255,
    "global_title_name": 255,
    "original_title": 255,
    "genre_name": 100,
    "country_name": 100,
    "person_full_name": 200,
    "primary_role": 50,
    "role_name": 50,
    "platform_show_id": 50,
    "duration_raw": 50
}

def safe_truncate(s, max_len):
    if s is None:
        return None
    s = str(s)
    return s if len(s) <= max_len else s[:max_len]

# ===============================
# 2. FILE CONFIG
# ===============================

# Map each CSV file to the streaming service name (corrected)
CSV_FILES = [
    {
        "path": r"../raw_data/amazon_prime_titles.csv",
        "service_name": "Amazon Prime Video"
    },
    {
        "path": r"../raw_data/disney_plus_titles.csv",
        "service_name": "Disney+"
    },
    {
        "path": r"../raw_data/hulu_titles.csv",
        "service_name": "Hulu"
    },
    {
        "path": r"../raw_data/netflix_titles.csv",
        "service_name": "Netflix"
    }
]

# ===============================
# 3. CACHES TO REDUCE QUERIES
# ===============================

rating_cache = {}
service_cache = {}
genre_cache = {}
country_cache = {}
role_type_cache = {}
person_cache = {}
title_cache = {}  # key: (global_title_name, release_year) -> title_id


# ===============================
# 4. HELPER FUNCTIONS
# ===============================

def get_connection():
    return pymysql.connect(charset="utf8mb4", cursorclass=pymysql.cursors.Cursor, **DB_CONFIG)


def normalize_string(s):
    if pd.isna(s):
        return None
    s = str(s).strip()
    return s if s else None


def parse_date(date_str):
    """Parse date_added like 'September 9, 2019' into YYYY-MM-DD or None."""
    if pd.isna(date_str) or not str(date_str).strip():
        return None
    try:
        dt = pd.to_datetime(date_str, errors="coerce")
        if pd.isna(dt):
            return None
        return dt.date()
    except Exception:
        return None


def parse_duration_for_title(content_type, duration_raw):
    """
    duration_raw examples:
        '90 min'            -> (runtime_minutes=90, num_seasons=None)
        '2 Seasons'         -> (runtime_minutes=None, num_seasons=2)
    """
    if pd.isna(duration_raw) or not str(duration_raw).strip():
        return (None, None)

    text = str(duration_raw).strip()
    # Extract first integer
    match = re.search(r"(\d+)", text)
    if not match:
        return (None, None)

    value = int(match.group(1))
    if content_type.upper() == "MOVIE":
        return (value, None)
    else:
        # For TV Shows, assume it's seasons
        return (None, value)


# ---------- DB lookups / inserts with caching ----------

def get_or_create_streaming_service(cursor, service_name):
    service_name_norm = safe_truncate(normalize_string(service_name), MAX_LENGTHS["service_name"])
    if service_name_norm in service_cache:
        return service_cache[service_name_norm]

    # Try select
    cursor.execute(
        "SELECT streaming_service_id FROM streaming_service WHERE service_name = %s",
        (service_name_norm,)
    )
    row = cursor.fetchone()
    if row:
        service_id = row[0]
        service_cache[service_name_norm] = service_id
        return service_id

    # Insert
    cursor.execute(
        "INSERT INTO streaming_service (service_name) VALUES (%s)",
        (service_name_norm,)
    )
    service_id = cursor.lastrowid
    service_cache[service_name_norm] = service_id
    return service_id


def get_or_create_rating(cursor, rating_code):
    code = safe_truncate(normalize_string(rating_code), MAX_LENGTHS["rating_code"])
    if not code:
        code = "UNRATED"

    if code in rating_cache:
        return code

    cursor.execute("SELECT rating_code FROM rating WHERE rating_code = %s", (code,))
    row = cursor.fetchone()
    if row:
        rating_cache[code] = True
        return code

    cursor.execute(
        "INSERT INTO rating (rating_code, age_minimum) VALUES (%s, %s)",
        (code, None)  # you can infer age_minimum later if desired
    )
    rating_cache[code] = True
    return code


def get_or_create_genre(cursor, genre_name):
    if genre_name is None:
        return None
    name = safe_truncate(normalize_string(genre_name), MAX_LENGTHS["genre_name"])
    if not name:
        return None

    if name in genre_cache:
        return genre_cache[name]

    cursor.execute(
        "SELECT genre_id FROM genre WHERE genre_name = %s",
        (name,)
    )
    row = cursor.fetchone()
    if row:
        gid = row[0]
        genre_cache[name] = gid
        return gid

    cursor.execute(
        "INSERT INTO genre (genre_name) VALUES (%s)",
        (name,)
    )
    gid = cursor.lastrowid
    genre_cache[name] = gid
    return gid


def get_or_create_country(cursor, country_name):
    if country_name is None:
        return None
    name = safe_truncate(normalize_string(country_name), MAX_LENGTHS["country_name"])
    if not name:
        return None

    if name in country_cache:
        return country_cache[name]

    cursor.execute(
        "SELECT country_id FROM country WHERE country_name = %s",
        (name,)
    )
    row = cursor.fetchone()
    if row:
        cid = row[0]
        country_cache[name] = cid
        return cid

    cursor.execute(
        "INSERT INTO country (country_name) VALUES (%s)",
        (name,)
    )
    cid = cursor.lastrowid
    country_cache[name] = cid
    return cid


def get_or_create_role_type(cursor, role_name):
    name = safe_truncate(normalize_string(role_name), MAX_LENGTHS["role_name"])
    if not name:
        return None

    if name in role_type_cache:
        return role_type_cache[name]

    cursor.execute(
        "SELECT role_type_id FROM role_type WHERE role_name = %s",
        (name,)
    )
    row = cursor.fetchone()
    if row:
        rid = row[0]
        role_type_cache[name] = rid
        return rid

    cursor.execute(
        "INSERT INTO role_type (role_name) VALUES (%s)",
        (name,)
    )
    rid = cursor.lastrowid
    role_type_cache[name] = rid
    return rid


def get_or_create_person(cursor, full_name, primary_role=None):
    if full_name is None:
        return None
    name = safe_truncate(normalize_string(full_name), MAX_LENGTHS["person_full_name"])
    if not name:
        return None

    if name in person_cache:
        return person_cache[name]

    cursor.execute(
        "SELECT person_id FROM person WHERE full_name = %s",
        (name,)
    )
    row = cursor.fetchone()
    if row:
        pid = row[0]
        person_cache[name] = pid
        return pid

    cursor.execute(
        "INSERT INTO person (full_name, primary_role) VALUES (%s, %s)",
        (name, primary_role)
    )
    pid = cursor.lastrowid
    person_cache[name] = pid
    return pid


def get_or_create_title(cursor, global_title_name, original_title, release_year,
                        age_rating_code, content_type, runtime_minutes, num_seasons):
    global_title_name = safe_truncate(normalize_string(global_title_name), MAX_LENGTHS["global_title_name"])
    original_title = safe_truncate(normalize_string(original_title), MAX_LENGTHS["original_title"])
    key = (global_title_name, release_year)
    if key in title_cache:
        return title_cache[key]

    cursor.execute(
        """
        SELECT title_id
        FROM title
        WHERE global_title_name = %s AND release_year = %s
        """,
        (global_title_name, release_year)
    )
    row = cursor.fetchone()
    if row:
        tid = row[0]
        title_cache[key] = tid
        return tid

    cursor.execute(
        """
        INSERT INTO title
            (global_title_name, original_title, description, release_year,
             age_rating_code, content_type, runtime_minutes, num_seasons)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (global_title_name, original_title, None, release_year,
         age_rating_code, content_type, runtime_minutes, num_seasons)
    )
    tid = cursor.lastrowid
    title_cache[key] = tid
    return tid


def insert_movie_subtype(cursor, title_id, movie_runtime_minutes):
    cursor.execute(
        "INSERT IGNORE INTO movie (title_id, movie_runtime_minutes) VALUES (%s, %s)",
        (title_id, movie_runtime_minutes)
    )


def insert_tv_show_subtype(cursor, title_id, total_seasons, episode_count=None):
    cursor.execute(
        "INSERT IGNORE INTO tv_show (title_id, total_seasons, episode_count) VALUES (%s, %s, %s)",
        (title_id, total_seasons, episode_count)
    )


def link_title_genres(cursor, title_id, genres_str):
    if pd.isna(genres_str) or not str(genres_str).strip():
        return
    genres = [g.strip() for g in str(genres_str).split(",") if g.strip()]
    for g in genres:
        gid = get_or_create_genre(cursor, g)
        if gid is None:
            continue
        cursor.execute(
            "INSERT IGNORE INTO title_genre (title_id, genre_id) VALUES (%s, %s)",
            (title_id, gid)
        )


def link_title_countries(cursor, title_id, countries_str):
    if pd.isna(countries_str) or not str(countries_str).strip():
        return
    countries = [c.strip() for c in str(countries_str).split(",") if c.strip()]
    for c in countries:
        cid = get_or_create_country(cursor, c)
        if cid is None:
            continue
        cursor.execute(
            "INSERT IGNORE INTO title_country (title_id, country_id) VALUES (%s, %s)",
            (title_id, cid)
        )


def link_title_persons(cursor, title_id, director_str, cast_str):
    # Make sure basic role types exist
    director_role_id = get_or_create_role_type(cursor, "Director")
    actor_role_id = get_or_create_role_type(cursor, "Actor")

    # Directors (sanity: only first director; keep first + last tokens; truncate)
    if director_str and not pd.isna(director_str):
        first_segment = str(director_str).split(",")[0].strip()
        tokens = [t for t in first_segment.split() if t]
        if len(tokens) >= 2:
            cleaned_director = f"{tokens[0]} {tokens[1]}"
        else:
            cleaned_director = tokens[0] if tokens else first_segment
        cleaned_director = safe_truncate(cleaned_director, MAX_LENGTHS["person_full_name"])
        pid = get_or_create_person(cursor, cleaned_director, primary_role="Director")
        if pid and director_role_id:
            cursor.execute(
                """
                INSERT IGNORE INTO title_person_role
                    (title_id, person_id, role_type_id, billing_order)
                VALUES (%s, %s, %s, %s)
                """,
                (title_id, pid, director_role_id, None)
            )

    # Cast
    if cast_str and not pd.isna(cast_str):
        # billing_order = index in the cast list
        actors = [a.strip() for a in str(cast_str).split(",") if a.strip()]
        for order, a in enumerate(actors, start=1):
            actor_name = safe_truncate(a, MAX_LENGTHS["person_full_name"])  # ensure fits
            pid = get_or_create_person(cursor, actor_name, primary_role="Actor")
            if pid and actor_role_id:
                cursor.execute(
                    """
                    INSERT IGNORE INTO title_person_role
                        (title_id, person_id, role_type_id, billing_order)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (title_id, pid, actor_role_id, order)
                )


def insert_streaming_availability(cursor, streaming_service_id, title_id,
                                  platform_show_id, date_added, duration_raw,
                                  is_exclusive=False, availability_status="ACTIVE"):
    platform_show_id = safe_truncate(platform_show_id, MAX_LENGTHS["platform_show_id"])
    duration_raw = safe_truncate(duration_raw, MAX_LENGTHS["duration_raw"])
    cursor.execute(
        """
        INSERT IGNORE INTO streaming_availability
            (streaming_service_id, title_id, platform_show_id,
             date_added, duration_raw, is_exclusive, availability_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            streaming_service_id,
            title_id,
            platform_show_id,
            date_added,
            duration_raw,
            int(is_exclusive),
            availability_status
        )
    )


# ===============================
# 5. MAIN ETL LOGIC
# ===============================

def process_csv_file(cursor, file_path, service_name):
    print(f"\nProcessing file: {file_path} for service: {service_name}")
    df = pd.read_csv(file_path)

    # Optional: clean up columns we care about
    expected_cols = [
        "show_id", "type", "title", "director", "cast", "country",
        "date_added", "release_year", "rating", "duration", "listed_in",
        "description"
    ]
    missing = [c for c in expected_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing expected columns in {file_path}: {missing}")

    # Get or create streaming service id
    service_id = get_or_create_streaming_service(cursor, service_name)

    row_count = 0

    for _, row in df.iterrows():
        row_count += 1

        platform_show_id = normalize_string(row["show_id"])
        raw_type = normalize_string(row["type"])  # 'Movie' or 'TV Show'
        title_str = normalize_string(row["title"])
        director_str = normalize_string(row["director"])
        cast_str = normalize_string(row["cast"])
        country_str = normalize_string(row["country"])
        date_added = parse_date(row["date_added"])
        release_year = int(row["release_year"]) if not pd.isna(row["release_year"]) else None
        rating_code = normalize_string(row["rating"])
        duration_raw = normalize_string(row["duration"])
        listed_in = normalize_string(row["listed_in"])
        description = normalize_string(row["description"])

        if not title_str or not release_year:
            # Skip weird/incomplete rows
            continue

        # Ensure rating row exists
        rating_code = get_or_create_rating(cursor, rating_code)

        # Content type mapping to enum
        if raw_type and raw_type.upper().startswith("MOVIE"):
            content_type = "MOVIE"
        else:
            content_type = "TV_SHOW"

        # Parse duration into runtime_minutes / num_seasons
        runtime_minutes, num_seasons = parse_duration_for_title(content_type, duration_raw)

        # Create or get Title
        global_title_name = title_str  # You can normalize more if desired
        original_title = title_str

        title_id = get_or_create_title(
            cursor,
            global_title_name=global_title_name,
            original_title=original_title,
            release_year=release_year,
            age_rating_code=rating_code,
            content_type=content_type,
            runtime_minutes=runtime_minutes,
            num_seasons=num_seasons
        )

        # Update description if still NULL in DB and we have one
        if description:
            cursor.execute(
                "UPDATE title SET description = COALESCE(description, %s) WHERE title_id = %s",
                (description, title_id)
            )

        # Insert subtype rows
        if content_type == "MOVIE":
            insert_movie_subtype(cursor, title_id, runtime_minutes)
        else:
            insert_tv_show_subtype(cursor, title_id, num_seasons, episode_count=None)

        # Link genres
        link_title_genres(cursor, title_id, listed_in)

        # Link countries
        link_title_countries(cursor, title_id, country_str)

        # Link people + roles
        link_title_persons(cursor, title_id, director_str, cast_str)

        # Insert streaming_availability
        if platform_show_id is None:
            # Use a fallback if show_id missing (rare)
            platform_show_id = f"{service_name[:3].upper()}_{title_id}"

        insert_streaming_availability(
            cursor,
            streaming_service_id=service_id,
            title_id=title_id,
            platform_show_id=platform_show_id,
            date_added=date_added,
            duration_raw=duration_raw,
            is_exclusive=False,              # You could compute this later
            availability_status="ACTIVE"
        )

        if row_count % 500 == 0:
            print(f"  Processed {row_count} rows from {file_path}...")

    print(f"Finished {file_path}: processed {row_count} rows.")


###############################
# 6. CONNECTION TEST
###############################

REQUIRED_TABLES = {
    "rating", "streaming_service", "title", "movie", "tv_show", "genre",
    "title_genre", "country", "title_country", "person", "role_type",
    "title_person_role", "streaming_availability"
}


def test_connection(verbose: bool = True) -> bool:
    """Attempt to connect and verify required tables exist."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = %s",
            (DB_CONFIG["database"],)
        )
        existing = {r[0] for r in cursor.fetchall()}
        missing = REQUIRED_TABLES - existing
        extra = existing - REQUIRED_TABLES
        if verbose:
            print(f"Connected to database '{DB_CONFIG['database']}' at {DB_CONFIG['host']}:{DB_CONFIG['port']}")
            print(f"Found {len(existing)} tables. Missing required: {len(missing)}")
            if missing:
                print(" Missing:", ", ".join(sorted(missing)))
            else:
                print(" All required tables present.")
            if extra:
                print(" Extra tables detected:", ", ".join(sorted(extra)))
        return not missing
    except pymysql_err.MySQLError as e:
        if verbose:
            print(f"Connection test failed: {e}")
        return False
    finally:
        try:
            cursor.close(); conn.close()
        except Exception:
            pass


###############################
# 7. DRY RUN (SIMULATED INSERTS)
###############################

def dry_run(sample_size: int = 5):
    """Simulate processing CSV files and show sample rows per target table without inserting."""
    print("Starting dry run (no data will be inserted)...")

    # Local caches (simulate empty DB)
    rating_set = set()
    service_set = set()
    title_map = {}  # key -> dict row
    movie_rows = []
    tv_show_rows = []
    genre_set = set()
    title_genre_rows = []  # (title_key, genre_name)
    country_set = set()
    title_country_rows = []  # (title_key, country_name)
    person_set = set()
    role_type_set = set()
    title_person_role_rows = []  # (title_key, person_name, role_name, billing_order)
    streaming_availability_rows = []  # dict rows

    for cfg in CSV_FILES:
        file_path = cfg["path"]
        service_name = cfg["service_name"]
        service_set.add(service_name)
        print(f" Reading CSV: {file_path} (service={service_name})")
        try:
            df = pd.read_csv(file_path)
        except FileNotFoundError:
            print(f"  WARNING: File not found, skipping: {file_path}")
            continue

        expected_cols = [
            "show_id", "type", "title", "director", "cast", "country",
            "date_added", "release_year", "rating", "duration", "listed_in",
            "description"
        ]
        missing = [c for c in expected_cols if c not in df.columns]
        if missing:
            print(f"  WARNING: Missing expected columns in {file_path}: {missing}")
            continue

        for _, row in df.iterrows():
            title_str = normalize_string(row["title"])
            release_year = int(row["release_year"]) if not pd.isna(row["release_year"]) else None
            if not title_str or not release_year:
                continue

            rating_code_raw = normalize_string(row["rating"]) or "UNRATED"
            rating_set.add(rating_code_raw)

            raw_type = normalize_string(row["type"]) or "TV Show"
            content_type = "MOVIE" if raw_type.upper().startswith("MOVIE") else "TV_SHOW"

            duration_raw = normalize_string(row["duration"])
            runtime_minutes, num_seasons = parse_duration_for_title(content_type, duration_raw)

            key = (title_str, release_year)
            if key not in title_map:
                title_map[key] = {
                    "global_title_name": title_str,
                    "original_title": title_str,
                    "description": normalize_string(row["description"]),
                    "release_year": release_year,
                    "age_rating_code": rating_code_raw,
                    "content_type": content_type,
                    "runtime_minutes": runtime_minutes,
                    "num_seasons": num_seasons
                }
                if content_type == "MOVIE":
                    movie_rows.append({"title_key": key, "movie_runtime_minutes": runtime_minutes})
                else:
                    tv_show_rows.append({"title_key": key, "total_seasons": num_seasons, "episode_count": None})

            # Genres
            listed_in = normalize_string(row["listed_in"]) or ""
            genres = [g.strip() for g in listed_in.split(",") if g.strip()]
            for g in genres:
                genre_set.add(g)
                title_genre_rows.append((key, g))

            # Countries
            country_str = normalize_string(row["country"]) or ""
            countries = [c.strip() for c in country_str.split(",") if c.strip()]
            for ctry in countries:
                country_set.add(ctry)
                title_country_rows.append((key, ctry))

            # People / roles
            director_str = normalize_string(row["director"]) or ""
            if director_str:
                directors = [d.strip() for d in director_str.split(",") if d.strip()]
                if directors:
                    role_type_set.add("Director")
                for d in directors:
                    person_set.add(d)
                    title_person_role_rows.append((key, d, "Director", None))
            cast_str = normalize_string(row["cast"]) or ""
            if cast_str:
                actors = [a.strip() for a in cast_str.split(",") if a.strip()]
                if actors:
                    role_type_set.add("Actor")
                for order, a in enumerate(actors, start=1):
                    person_set.add(a)
                    title_person_role_rows.append((key, a, "Actor", order))

            # Streaming availability simulated row
            date_added = parse_date(row["date_added"])
            streaming_availability_rows.append({
                "service_name": service_name,
                "title_key": key,
                "platform_show_id": normalize_string(row["show_id"]) or f"{service_name[:3].upper()}_{title_str[:10]}_{release_year}",
                "date_added": date_added,
                "duration_raw": duration_raw,
                "is_exclusive": 0,
                "availability_status": "ACTIVE"
            })

    def sample(rows):
        return rows[:sample_size]

    print("\n=== DRY RUN SUMMARY (simulated inserts) ===")

    print(f"rating: {len(rating_set)} codes")
    print(" sample:", sample(sorted(rating_set)))

    print(f"streaming_service: {len(service_set)} services")
    print(" sample:", sample(sorted(service_set)))

    print(f"title: {len(title_map)} titles")
    print(" sample:")
    for k, v in list(title_map.items())[:sample_size]:
        print("  ", k, v)

    print(f"movie: {len(movie_rows)} rows")
    for r in sample(movie_rows):
        print("  ", r)

    print(f"tv_show: {len(tv_show_rows)} rows")
    for r in sample(tv_show_rows):
        print("  ", r)

    print(f"genre: {len(genre_set)} unique")
    print(" sample:", sample(sorted(genre_set)))

    print(f"title_genre: {len(title_genre_rows)} links")
    for r in sample(title_genre_rows):
        print("  ", r)

    print(f"country: {len(country_set)} unique")
    print(" sample:", sample(sorted(country_set)))

    print(f"title_country: {len(title_country_rows)} links")
    for r in sample(title_country_rows):
        print("  ", r)

    print(f"person: {len(person_set)} unique")
    print(" sample:", sample(sorted(person_set)))

    print(f"role_type: {len(role_type_set)} unique")
    print(" sample:", sample(sorted(role_type_set)))

    print(f"title_person_role: {len(title_person_role_rows)} links")
    for r in sample(title_person_role_rows):
        print("  ", r)

    print(f"streaming_availability: {len(streaming_availability_rows)} rows")
    for r in sample(streaming_availability_rows):
        print("  ", r)

    print("\nDry run complete.")


###############################
# 8. LIVE RUN (ACTUAL INSERTS)
###############################

def live_run():
    try:
        if not test_connection(verbose=False):
            print("WARNING: Some required tables are missing. Proceeding anyway.")
        conn = get_connection()
        cursor = conn.cursor()
        for cfg in CSV_FILES:
            process_csv_file(cursor, cfg["path"], cfg["service_name"])
            conn.commit()
        print("\nAll files processed successfully.")
    except pymysql_err.MySQLError as e:
        print(f"Error connecting to MySQL or executing queries: {e}")
    finally:
        try:
            cursor.close(); conn.close()
        except Exception:
            pass


###############################
# 9. ARGUMENT PARSING ENTRYPOINT
###############################

def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="ETL for streaming service catalogs")
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--test-connection", action="store_true", help="Test DB connection and table presence")
    group.add_argument("--dry-run", action="store_true", help="Simulate inserts; show samples per table")
    group.add_argument("--live-run", action="store_true", help="Perform actual ETL inserts (default if none specified)")
    parser.add_argument("--sample-size", type=int, default=5, help="Sample size per table for dry run output")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.test_connection:
        ok = test_connection(verbose=True)
        sys.exit(0 if ok else 1)
    if args.dry_run:
        dry_run(sample_size=args.sample_size)
        return
    # Default to live run if neither flag specified or explicit --live-run
    live_run()


if __name__ == "__main__":
    main()

# Streaming Media Database Schema

This document summarizes the physical schema created by `documents/tv_movie_DDL.sql` for the `streaming_media_db` MySQL database. The design centers on the `title` supertype and its movie/TV subtypes plus associative tables that capture genres, countries, people/roles, and platform availability.

## Entity Overview
- `rating`: Normalizes parental guidance ratings and minimum suggested ages.
- `streaming_service`: Catalog of OTT providers (e.g., Netflix, Hulu) including metadata such as launch year and URL.
- `title`: Core record for every piece of content with normalized and original names, description, release year, rating, and discriminator columns.
- `movie` / `tv_show`: Subtype tables keyed 1:1 with `title` and storing runtime or episode metadata.
- `genre`, `title_genre`: Genre dimension and bridge capturing many-to-many relationships between titles and genres.
- `country`, `title_country`: Countries of production and bridge to titles.
- `person`, `role_type`, `title_person_role`: People, role taxonomy, and their participation on specific titles (cast/crew) with optional billing order.
- `streaming_availability`: Records which service carries which title, along with platform-specific identifiers, dates, exclusivity, and status flags.

## Table Details

### rating (`E7`)
| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `rating_code` | VARCHAR(10) | NO | Primary key; codes like `TV-MA`, `PG-13`. |
| `age_minimum` | TINYINT UNSIGNED | YES | Suggested minimum viewer age. |

- **Primary Key**: `pk_rating (rating_code)`.
- **Referenced By**: `title.age_rating_code` (cascade on update, restrict on delete).

### streaming_service (`E1`)
| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `streaming_service_id` | INT UNSIGNED AUTO_INCREMENT | NO | Surrogate primary key. |
| `service_name` | VARCHAR(100) | NO | Unique service name. |
| `country_of_operation` | VARCHAR(100) | YES | Headquarters or primary operating country. |
| `launch_year` | YEAR | YES | Year the platform launched. |
| `url` | VARCHAR(255) | YES | Marketing or catalog URL. |

- **Primary Key**: `pk_streaming_service (streaming_service_id)`.
- **Unique Constraint**: `uq_streaming_service_name (service_name)`.
- **Referenced By**: `streaming_availability.streaming_service_id`.

### title (`E2` supertype)
| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `title_id` | BIGINT UNSIGNED AUTO_INCREMENT | NO | Surrogate key shared by subtypes. |
| `global_title_name` | VARCHAR(255) | NO | Normalized name for deduplication. |
| `original_title` | VARCHAR(255) | YES | Raw/imported title if it differs. |
| `description` | TEXT | YES | Synopsis or blurb. |
| `release_year` | YEAR | NO | Four-digit release year. |
| `age_rating_code` | VARCHAR(10) | NO | FK → `rating.rating_code`. |
| `content_type` | ENUM('MOVIE','TV_SHOW') | NO | Discriminator identifying subtype. |
| `runtime_minutes` | SMALLINT UNSIGNED | YES | Generic runtime (movies). |
| `num_seasons` | SMALLINT UNSIGNED | YES | Generic season count (TV). |

- **Primary Key**: `pk_title (title_id)`.
- **Unique Constraint**: `uq_title_name_year (global_title_name, release_year)`.
- **Indexes**: `idx_title_content_type`, `idx_title_release_year`.
- **Foreign Keys**: `fk_title_rating` → `rating` (cascade update, restrict delete).
- **Referenced By**: `movie`, `tv_show`, `title_genre`, `title_country`, `title_person_role`, `streaming_availability`.

### movie (`E3` subtype)
| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `title_id` | BIGINT UNSIGNED | NO | PK/FK referencing `title`. |
| `movie_runtime_minutes` | SMALLINT UNSIGNED | YES | Optional override for runtime. |

- **Primary Key**: `pk_movie (title_id)`.
- **Foreign Key**: `fk_movie_title` → `title.title_id` (cascade update/delete).
- **Represents**: Rows where `title.content_type = 'MOVIE'`.

### tv_show (`E4` subtype)
| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `title_id` | BIGINT UNSIGNED | NO | PK/FK referencing `title`. |
| `total_seasons` | SMALLINT UNSIGNED | YES | Total produced seasons. |
| `episode_count` | SMALLINT UNSIGNED | YES | Total number of episodes. |

- **Primary Key**: `pk_tv_show (title_id)`.
- **Foreign Key**: `fk_tv_show_title` → `title.title_id` (cascade update/delete).
- **Represents**: Rows where `title.content_type = 'TV_SHOW'`.

### genre (`E5`)
| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `genre_id` | INT UNSIGNED AUTO_INCREMENT | NO | Surrogate key. |
| `genre_name` | VARCHAR(100) | NO | Unique genre label. |

- **Primary Key**: `pk_genre (genre_id)`.
- **Unique Constraint**: `uq_genre_name (genre_name)`.
- **Referenced By**: `title_genre.genre_id` (restrict delete).

### title_genre (`E6` bridge)
| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `title_id` | BIGINT UNSIGNED | NO | FK → `title`. |
| `genre_id` | INT UNSIGNED | NO | FK → `genre`. |

- **Primary Key**: `pk_title_genre (title_id, genre_id)`.
- **Foreign Keys**: `fk_title_genre_title`, `fk_title_genre_genre`.
- **Indexes**: `idx_title_genre_genre_id (genre_id)` for filtering by genre.
- **Purpose**: Many-to-many association between titles and genres (cascade delete when parent title is removed; restrict when genre still in use).

### country (`E8`)
| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `country_id` | INT UNSIGNED AUTO_INCREMENT | NO | Surrogate key. |
| `country_name` | VARCHAR(100) | NO | Unique country label. |

- **Primary Key**: `pk_country (country_id)`.
- **Unique Constraint**: `uq_country_name (country_name)`.
- **Referenced By**: `title_country.country_id` (restrict delete).

### title_country (`E9` bridge)
| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `title_id` | BIGINT UNSIGNED | NO | FK → `title`. |
| `country_id` | INT UNSIGNED | NO | FK → `country`. |

- **Primary Key**: `pk_title_country (title_id, country_id)`.
- **Foreign Keys**: `fk_title_country_title`, `fk_title_country_country`.
- **Indexes**: `idx_title_country_country_id` aids lookups by country.
- **Purpose**: Many-to-many association between titles and producing countries (cascade delete with titles, restrict on country).

### person (`E10`)
| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `person_id` | BIGINT UNSIGNED AUTO_INCREMENT | NO | Surrogate key. |
| `full_name` | VARCHAR(200) | NO | Indexed for lookup. |
| `date_of_birth` | DATE | YES | Optional. |
| `primary_role` | VARCHAR(50) | YES | Informational default role (Actor, Director, etc.). |

- **Primary Key**: `pk_person (person_id)`.
- **Indexes**: `idx_person_full_name` for text searches.
- **Referenced By**: `title_person_role.person_id` (restrict delete).

### role_type (`E11`)
| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `role_type_id` | INT UNSIGNED AUTO_INCREMENT | NO | Surrogate key. |
| `role_name` | VARCHAR(50) | NO | Unique role label. |

- **Primary Key**: `pk_role_type (role_type_id)`.
- **Unique Constraint**: `uq_role_name (role_name)`.
- **Referenced By**: `title_person_role.role_type_id` (restrict delete).

### title_person_role (`E12` bridge)
| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `title_id` | BIGINT UNSIGNED | NO | FK → `title`. |
| `person_id` | BIGINT UNSIGNED | NO | FK → `person`. |
| `role_type_id` | INT UNSIGNED | NO | FK → `role_type`. |
| `billing_order` | SMALLINT UNSIGNED | YES | Optional order for primary cast. |

- **Primary Key**: `pk_title_person_role (title_id, person_id, role_type_id)`.
- **Foreign Keys**: `fk_tpr_title` (cascade delete with title), `fk_tpr_person`, `fk_tpr_role_type` (restrict delete).
- **Indexes**: `idx_tpr_person_id`, `idx_tpr_role_type_id` for cast/crew queries.
- **Purpose**: Associative table capturing which people filled specific role types on each title.

### streaming_availability (`E13`)
| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `availability_id` | BIGINT UNSIGNED AUTO_INCREMENT | NO | Surrogate key. |
| `streaming_service_id` | INT UNSIGNED | NO | FK → `streaming_service`. |
| `title_id` | BIGINT UNSIGNED | NO | FK → `title`. |
| `platform_show_id` | VARCHAR(50) | NO | Provider-specific ID; unique per service. |
| `date_added` | DATE | YES | When the title was added to the service. |
| `duration_raw` | VARCHAR(50) | YES | Raw duration string from source CSV. |
| `is_exclusive` | TINYINT(1) | NO | Boolean flag (0/1) for exclusivity. |
| `availability_status` | ENUM('ACTIVE','EXPIRED') | NO | Current availability state, default `ACTIVE`. |

- **Primary Key**: `pk_streaming_availability (availability_id)`.
- **Unique Constraints**:
  - `uq_sa_service_platform_show (streaming_service_id, platform_show_id)` ensures provider IDs are unique per service.
  - `uq_sa_service_title (streaming_service_id, title_id)` enforces at most one record per service/title combination.
- **Foreign Keys**: `fk_sa_streaming_service` (restrict delete) and `fk_sa_title` (cascade delete with title).
- **Indexes**: `idx_sa_title_id`, `idx_sa_service_id` support filtering by either axis.

## Relationship Highlights
- **Inheritance**: `title` is the parent for `movie` and `tv_show`. Each title row should appear in exactly one subtype table determined by `content_type`.
- **Dimensional Bridges**: `title_genre`, `title_country`, and `title_person_role` implement many-to-many relationships between titles and their associated genres, countries, and people/roles, respectively.
- **Availability**: `streaming_availability` ties together services and titles, tracking platform-specific identifiers, dates, exclusivity, and status.
- **Reference Integrity**: Most child tables cascade updates and deletes when the parent is a title (so removing a title automatically removes dependent rows), while lookup dimensions such as `genre`, `country`, `person`, and `role_type` use `ON DELETE RESTRICT` to protect shared reference data.

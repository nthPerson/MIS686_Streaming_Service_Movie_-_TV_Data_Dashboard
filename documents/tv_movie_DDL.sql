-- Optional: create and select a database for this project
CREATE DATABASE IF NOT EXISTS streaming_media_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE streaming_media_db;

-- Safety: drop existing tables in dependency-safe order
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS streaming_availability;
DROP TABLE IF EXISTS title_person_role;
DROP TABLE IF EXISTS title_country;
DROP TABLE IF EXISTS title_genre;
DROP TABLE IF EXISTS tv_show;
DROP TABLE IF EXISTS movie;
DROP TABLE IF EXISTS role_type;
DROP TABLE IF EXISTS person;
DROP TABLE IF EXISTS country;
DROP TABLE IF EXISTS genre;
DROP TABLE IF EXISTS title;
DROP TABLE IF EXISTS streaming_service;
DROP TABLE IF EXISTS rating;

SET FOREIGN_KEY_CHECKS = 1;

------------------------------------------------------------
-- [E7] Rating
------------------------------------------------------------
CREATE TABLE rating (
    rating_code      VARCHAR(10)  NOT NULL,            -- e.g. 'TV-MA', 'PG-13'
    age_minimum      TINYINT UNSIGNED NULL,            -- e.g. 17

    CONSTRAINT pk_rating PRIMARY KEY (rating_code)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4;

------------------------------------------------------------
-- [E1] StreamingService
------------------------------------------------------------
CREATE TABLE streaming_service (
    streaming_service_id   INT UNSIGNED NOT NULL AUTO_INCREMENT,
    service_name           VARCHAR(100) NOT NULL,      -- e.g. 'Netflix', 'Amazon Prime Video'
    country_of_operation   VARCHAR(100) NULL,
    launch_year            YEAR NULL,
    url                    VARCHAR(255) NULL,

    CONSTRAINT pk_streaming_service PRIMARY KEY (streaming_service_id),
    CONSTRAINT uq_streaming_service_name UNIQUE (service_name)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4;

------------------------------------------------------------
-- [E2] Title (supertype)
------------------------------------------------------------
CREATE TABLE title (
    title_id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    global_title_name VARCHAR(255) NOT NULL,           -- normalized name
    original_title   VARCHAR(255) NULL,                -- raw/original name, if different
    description      TEXT NULL,
    release_year     YEAR NOT NULL,
    age_rating_code  VARCHAR(10) NOT NULL,             -- FK -> rating.rating_code
    content_type     ENUM('MOVIE','TV_SHOW') NOT NULL,
    runtime_minutes  SMALLINT UNSIGNED NULL,           -- movie; nullable
    num_seasons      SMALLINT UNSIGNED NULL,           -- tv shows; nullable

    CONSTRAINT pk_title PRIMARY KEY (title_id),

    -- Many titles can share same name in different years, but this helps deduplicate imports
    CONSTRAINT uq_title_name_year UNIQUE (global_title_name, release_year),

    CONSTRAINT fk_title_rating
        FOREIGN KEY (age_rating_code)
        REFERENCES rating (rating_code)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4;

CREATE INDEX idx_title_content_type ON title (content_type);
CREATE INDEX idx_title_release_year ON title (release_year);

------------------------------------------------------------
-- [E3] Movie (subtype of Title)
------------------------------------------------------------
CREATE TABLE movie (
    title_id              BIGINT UNSIGNED NOT NULL,    -- also PK, FK -> title
    movie_runtime_minutes SMALLINT UNSIGNED NULL,      -- movie-specific runtime if you want

    CONSTRAINT pk_movie PRIMARY KEY (title_id),

    CONSTRAINT fk_movie_title
        FOREIGN KEY (title_id)
        REFERENCES title (title_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4;

------------------------------------------------------------
-- [E4] TVShow (subtype of Title)
------------------------------------------------------------
CREATE TABLE tv_show (
    title_id       BIGINT UNSIGNED NOT NULL,           -- also PK, FK -> title
    total_seasons  SMALLINT UNSIGNED NULL,
    episode_count  SMALLINT UNSIGNED NULL,

    CONSTRAINT pk_tv_show PRIMARY KEY (title_id),

    CONSTRAINT fk_tv_show_title
        FOREIGN KEY (title_id)
        REFERENCES title (title_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4;

------------------------------------------------------------
-- [E5] Genre
------------------------------------------------------------
CREATE TABLE genre (
    genre_id    INT UNSIGNED NOT NULL AUTO_INCREMENT,
    genre_name  VARCHAR(100) NOT NULL,                 -- e.g. 'Drama', 'Kids’ TV'

    CONSTRAINT pk_genre PRIMARY KEY (genre_id),
    CONSTRAINT uq_genre_name UNIQUE (genre_name)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4;

------------------------------------------------------------
-- [E6] TitleGenre (associative: Title <-> Genre)
------------------------------------------------------------
CREATE TABLE title_genre (
    title_id  BIGINT UNSIGNED NOT NULL,
    genre_id  INT UNSIGNED NOT NULL,

    CONSTRAINT pk_title_genre PRIMARY KEY (title_id, genre_id),

    CONSTRAINT fk_title_genre_title
        FOREIGN KEY (title_id)
        REFERENCES title (title_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT fk_title_genre_genre
        FOREIGN KEY (genre_id)
        REFERENCES genre (genre_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4;

CREATE INDEX idx_title_genre_genre_id ON title_genre (genre_id);

------------------------------------------------------------
-- [E8] Country
------------------------------------------------------------
CREATE TABLE country (
    country_id    INT UNSIGNED NOT NULL AUTO_INCREMENT,
    country_name  VARCHAR(100) NOT NULL,              -- e.g. 'United States', 'India'

    CONSTRAINT pk_country PRIMARY KEY (country_id),
    CONSTRAINT uq_country_name UNIQUE (country_name)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4;

------------------------------------------------------------
-- [E9] TitleCountry (associative: Title <-> Country)
------------------------------------------------------------
CREATE TABLE title_country (
    title_id    BIGINT UNSIGNED NOT NULL,
    country_id  INT UNSIGNED NOT NULL,

    CONSTRAINT pk_title_country PRIMARY KEY (title_id, country_id),

    CONSTRAINT fk_title_country_title
        FOREIGN KEY (title_id)
        REFERENCES title (title_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT fk_title_country_country
        FOREIGN KEY (country_id)
        REFERENCES country (country_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4;

CREATE INDEX idx_title_country_country_id ON title_country (country_id);

------------------------------------------------------------
-- [E10] Person
------------------------------------------------------------
CREATE TABLE person (
    person_id     BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    full_name     VARCHAR(200) NOT NULL,
    date_of_birth DATE NULL,
    primary_role  VARCHAR(50) NULL,                     -- e.g. 'Actor', 'Director'

    CONSTRAINT pk_person PRIMARY KEY (person_id)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4;

CREATE INDEX idx_person_full_name ON person (full_name);

------------------------------------------------------------
-- [E11] RoleType
------------------------------------------------------------
CREATE TABLE role_type (
    role_type_id  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    role_name     VARCHAR(50) NOT NULL,                 -- 'Actor', 'Director', etc.

    CONSTRAINT pk_role_type PRIMARY KEY (role_type_id),
    CONSTRAINT uq_role_name UNIQUE (role_name)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4;

------------------------------------------------------------
-- [E12] TitlePersonRole (associative: Title <-> Person <-> RoleType)
------------------------------------------------------------
CREATE TABLE title_person_role (
    title_id      BIGINT UNSIGNED NOT NULL,
    person_id     BIGINT UNSIGNED NOT NULL,
    role_type_id  INT UNSIGNED NOT NULL,
    billing_order SMALLINT UNSIGNED NULL,               -- for top-billed cast, etc.

    CONSTRAINT pk_title_person_role PRIMARY KEY (title_id, person_id, role_type_id),

    CONSTRAINT fk_tpr_title
        FOREIGN KEY (title_id)
        REFERENCES title (title_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT fk_tpr_person
        FOREIGN KEY (person_id)
        REFERENCES person (person_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_tpr_role_type
        FOREIGN KEY (role_type_id)
        REFERENCES role_type (role_type_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4;

CREATE INDEX idx_tpr_person_id ON title_person_role (person_id);
CREATE INDEX idx_tpr_role_type_id ON title_person_role (role_type_id);

------------------------------------------------------------
-- [E13] StreamingAvailability
------------------------------------------------------------
CREATE TABLE streaming_availability (
    availability_id      BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    streaming_service_id INT UNSIGNED NOT NULL,
    title_id             BIGINT UNSIGNED NOT NULL,
    platform_show_id     VARCHAR(50) NOT NULL,          -- original show_id from CSV
    date_added           DATE NULL,
    duration_raw         VARCHAR(50) NULL,              -- raw '90 min', '3 Seasons', etc.
    is_exclusive         TINYINT(1) NOT NULL DEFAULT 0,
    availability_status  ENUM('ACTIVE','EXPIRED') NOT NULL DEFAULT 'ACTIVE',

    CONSTRAINT pk_streaming_availability PRIMARY KEY (availability_id),

    -- A given platform_show_id should be unique within a service
    CONSTRAINT uq_sa_service_platform_show
        UNIQUE (streaming_service_id, platform_show_id),

    -- One title per service row (if same title appears multiple times per service, adjust as needed)
    CONSTRAINT uq_sa_service_title
        UNIQUE (streaming_service_id, title_id),

    CONSTRAINT fk_sa_streaming_service
        FOREIGN KEY (streaming_service_id)
        REFERENCES streaming_service (streaming_service_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_sa_title
        FOREIGN KEY (title_id)
        REFERENCES title (title_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4;

CREATE INDEX idx_sa_title_id ON streaming_availability (title_id);
CREATE INDEX idx_sa_service_id ON streaming_availability (streaming_service_id);

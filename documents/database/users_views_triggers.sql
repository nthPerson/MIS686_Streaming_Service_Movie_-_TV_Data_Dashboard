USE streaming_media_db;

-- ---------------------------------------------------------
-- 1. Application-level roles and users
-- ---------------------------------------------------------

-- 1.1 app_role: lookup for application roles
CREATE TABLE IF NOT EXISTS app_role (
    role_id     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    role_name   VARCHAR(50) NOT NULL,          -- 'admin', 'analyst', 'viewer'

    CONSTRAINT pk_app_role PRIMARY KEY (role_id),
    CONSTRAINT uq_app_role_name UNIQUE (role_name)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4;

-- Seed a few default roles
INSERT INTO app_role (role_name)
VALUES ('admin'), ('analyst'), ('viewer')
ON DUPLICATE KEY UPDATE role_name = VALUES(role_name);


-- 1.2 app_user: application users (for Streamlit authentication)
CREATE TABLE IF NOT EXISTS app_user (
    user_id        BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    username       VARCHAR(100) NOT NULL,
    email          VARCHAR(255) NOT NULL,
    password_hash  VARCHAR(255) NOT NULL,   -- store bcrypt/argon2 hash
    role_id        INT UNSIGNED NOT NULL,   -- FK -> app_role
    is_active      TINYINT(1) NOT NULL DEFAULT 1,
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at  DATETIME NULL,

    CONSTRAINT pk_app_user PRIMARY KEY (user_id),
    CONSTRAINT uq_app_user_username UNIQUE (username),
    CONSTRAINT uq_app_user_email UNIQUE (email),

    CONSTRAINT fk_app_user_role
        FOREIGN KEY (role_id)
        REFERENCES app_role (role_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4;



-- ---------------------------------------------------------
-- 2. View: platform comparison (titles + movie/TV counts)
-- ---------------------------------------------------------
-- Summarizes how many MOVIE vs TV_SHOW titles each service has.

CREATE OR REPLACE VIEW vw_service_content_summary AS
SELECT
    s.streaming_service_id,
    s.service_name,
    t.content_type,
    COUNT(DISTINCT t.title_id) AS title_count
FROM streaming_availability sa
JOIN streaming_service s
  ON sa.streaming_service_id = s.streaming_service_id
JOIN title t
  ON sa.title_id = t.title_id
GROUP BY s.streaming_service_id, s.service_name, t.content_type;



-- ---------------------------------------------------------
-- 3. Stored procedure: parameterized service / type / year filter
-- ---------------------------------------------------------
-- Returns titles filtered by:
--   - service name (nullable)
--   - content type (MOVIE / TV_SHOW, nullable)
--   - release year range (nullable)

DELIMITER $$

CREATE PROCEDURE sp_get_titles_for_dashboard (
    IN p_service_name       VARCHAR(100),
    IN p_content_type       ENUM('MOVIE','TV_SHOW'),
    IN p_release_year_start INT,
    IN p_release_year_end   INT
)
BEGIN
    SELECT
        s.service_name,
        t.title_id,
        t.global_title_name,
        t.content_type,
        t.release_year,
        t.runtime_minutes,
        t.num_seasons
    FROM streaming_availability sa
    JOIN streaming_service s
      ON sa.streaming_service_id = s.streaming_service_id
    JOIN title t
      ON sa.title_id = t.title_id
    WHERE (p_service_name IS NULL OR s.service_name = p_service_name)
      AND (p_content_type IS NULL OR t.content_type = p_content_type)
      AND (p_release_year_start IS NULL OR t.release_year >= p_release_year_start)
      AND (p_release_year_end   IS NULL OR t.release_year <= p_release_year_end)
    ORDER BY s.service_name, t.release_year, t.global_title_name;
END$$

DELIMITER ;



-- ---------------------------------------------------------
-- 4. User-creation audit: table + trigger (Option 1)
-- ---------------------------------------------------------
-- Logs whenever a new app_user row is inserted.

CREATE TABLE IF NOT EXISTS app_user_audit (
    audit_id      BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id       BIGINT UNSIGNED NOT NULL,
    action        ENUM('CREATE','UPDATE','DELETE') NOT NULL,
    old_role_id   INT UNSIGNED NULL,
    new_role_id   INT UNSIGNED NULL,
    changed_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    changed_by    VARCHAR(100) NOT NULL,  -- MySQL CURRENT_USER()
    PRIMARY KEY (audit_id)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4;

DELIMITER $$

CREATE TRIGGER trg_app_user_after_insert
AFTER INSERT ON app_user
FOR EACH ROW
BEGIN
    INSERT INTO app_user_audit (
        user_id,
        action,
        old_role_id,
        new_role_id,
        changed_by
    )
    VALUES (
        NEW.user_id,
        'CREATE',
        NULL,
        NEW.role_id,
        CURRENT_USER()
    );
END$$

DELIMITER ;

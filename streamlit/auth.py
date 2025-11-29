"""Lightweight helpers for user registration and authentication."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Dict, Tuple

from mysql.connector import errors

from db import get_connection, run_query


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: int
    username: str
    email: str
    role: str


def _hash_password(password: str) -> str:
    # Simple SHA-256 hash for the toy environment; replace with bcrypt/argon2 in production.
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def list_roles() -> list[str]:
    roles_df = run_query("SELECT role_name FROM app_role ORDER BY role_name")
    if roles_df.empty:
        return ["viewer"]
    return roles_df["role_name"].tolist()


def register_user(username: str, email: str, password: str, role_name: str) -> Tuple[bool, str]:
    hashed = _hash_password(password)
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT role_id FROM app_role WHERE role_name = %s", (role_name,))
            role_row = cursor.fetchone()
            if not role_row:
                cursor.close()
                return False, "Selected role is no longer available."

            role_id = role_row[0]
            cursor.execute(
                """
                INSERT INTO app_user (username, email, password_hash, role_id)
                VALUES (%s, %s, %s, %s)
                """,
                (username, email, hashed, role_id),
            )
            connection.commit()
            cursor.close()
        return True, "Account created! You can log in now."
    except errors.IntegrityError as exc:
        message = "Username or email already exists."
        if exc.errno == 1062:
            if "username" in str(exc).lower():
                message = "That username is already taken."
            elif "email" in str(exc).lower():
                message = "That email is already registered."
        return False, message
    except Exception as exc:  # pragma: no cover - logged by caller
        return False, f"Unable to create account: {exc}"


def authenticate_user(username: str, password: str) -> Tuple[bool, str, AuthenticatedUser | None]:
    hashed = _hash_password(password)
    with get_connection() as connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT au.user_id, au.username, au.email, ar.role_name
            FROM app_user au
            JOIN app_role ar ON ar.role_id = au.role_id
            WHERE au.username = %s AND au.password_hash = %s AND au.is_active = 1
            """,
            (username, hashed),
        )
        row: Dict | None = cursor.fetchone()
        if not row:
            cursor.close()
            return False, "Invalid username or password.", None

        cursor.execute("UPDATE app_user SET last_login_at = NOW() WHERE user_id = %s", (row["user_id"],))
        connection.commit()
        cursor.close()

    user = AuthenticatedUser(
        user_id=row["user_id"],
        username=row["username"],
        email=row["email"],
        role=row["role_name"],
    )
    return True, f"Welcome back, {user.username}!", user
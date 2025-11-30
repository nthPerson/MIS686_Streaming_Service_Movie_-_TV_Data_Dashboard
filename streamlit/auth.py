"""Lightweight helpers for user registration and authentication."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from db import get_session
from models import AppRole, AppUser, AppUserAudit


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
    with get_session() as session:
        roles = session.scalars(select(AppRole.role_name).order_by(AppRole.role_name)).all()
    return roles or ["viewer"]


def register_user(username: str, email: str, password: str, role_name: str) -> Tuple[bool, str]:
    hashed = _hash_password(password)
    try:
        with get_session() as session:
            role = session.scalar(select(AppRole).where(AppRole.role_name == role_name))
            if role is None:
                return False, "Selected role is no longer available."

            new_user = AppUser(
                username=username,
                email=email,
                password_hash=hashed,
                role_id=role.role_id,
            )
            session.add(new_user)
        return True, "Account created! You can log in now."
    except IntegrityError as exc:
        message = "Username or email already exists."
        detail = str(exc.orig).lower() if exc.orig else ""
        if "username" in detail:
            message = "That username is already taken."
        elif "email" in detail:
            message = "That email is already registered."
        return False, message
    except Exception as exc:  # pragma: no cover - logged by caller
        return False, f"Unable to create account: {exc}"


def authenticate_user(username: str, password: str) -> Tuple[bool, str, AuthenticatedUser | None]:
    hashed = _hash_password(password)
    with get_session() as session:
        stmt = (
            select(AppUser, AppRole.role_name)
            .join(AppRole, AppRole.role_id == AppUser.role_id)
            .where(AppUser.username == username, AppUser.password_hash == hashed, AppUser.is_active.is_(True))
        )
        result = session.execute(stmt).first()
        if not result:
            return False, "Invalid username or password.", None

        user_row, role_name = result
        user_row.last_login_at = datetime.utcnow()

    user = AuthenticatedUser(
        user_id=user_row.user_id,
        username=user_row.username,
        email=user_row.email,
        role=role_name,
    )
    return True, f"Welcome back, {user.username}!", user


def fetch_users() -> List[dict]:
    with get_session() as session:
        results = session.execute(
            select(
                AppUser.user_id,
                AppUser.username,
                AppUser.email,
                AppUser.is_active,
                AppUser.created_at,
                AppUser.last_login_at,
                AppRole.role_name,
            )
            .join(AppRole, AppRole.role_id == AppUser.role_id)
            .order_by(AppUser.username)
        ).mappings().all()
    return [dict(row) for row in results]


def update_user_role(user_id: int, role_name: str) -> Tuple[bool, str]:
    with get_session() as session:
        role = session.scalar(select(AppRole).where(AppRole.role_name == role_name))
        if not role:
            return False, "Role not found."

        user = session.get(AppUser, user_id)
        if not user:
            return False, "User not found."

        user.role_id = role.role_id
    return True, "Role updated."


def toggle_user_active(user_id: int, is_active: bool) -> Tuple[bool, str]:
    with get_session() as session:
        user = session.get(AppUser, user_id)
        if not user:
            return False, "User not found."
        user.is_active = is_active
    return True, "User status updated."


def delete_user(user_id: int) -> Tuple[bool, str]:
    with get_session() as session:
        stmt = delete(AppUser).where(AppUser.user_id == user_id)
        result = session.execute(stmt)
        if result.rowcount == 0:
            return False, "User not found."
    return True, "User removed."


def fetch_user_audit() -> List[dict]:
    with get_session() as session:
        audits = session.execute(
            select(
                AppUserAudit.audit_id,
                AppUserAudit.user_id,
                AppUserAudit.action,
                AppUserAudit.old_role_id,
                AppUserAudit.new_role_id,
                AppUserAudit.changed_at,
                AppUserAudit.changed_by,
            )
            .order_by(AppUserAudit.changed_at.desc())
            .limit(200)
        ).mappings().all()
    return [dict(row) for row in audits]
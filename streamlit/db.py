"""Database helpers powered by SQLAlchemy."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator
from urllib.parse import quote_plus

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from config import AppSettings, get_settings

_ENGINE: Engine | None = None
_SESSION_FACTORY: sessionmaker | None = None


def _build_connection_string(settings: AppSettings) -> str:
    db = settings.database
    user = quote_plus(db.user)
    password = quote_plus(db.password)
    host = db.host
    port = db.port
    name = db.name
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}?charset=utf8mb4"


def get_engine() -> Engine:
    global _ENGINE
    if _ENGINE is None:
        settings = get_settings()
        _ENGINE = create_engine(
            _build_connection_string(settings),
            pool_pre_ping=True,
            pool_recycle=1800,
            future=True,
        )
    return _ENGINE


def _get_session_factory() -> sessionmaker:
    global _SESSION_FACTORY
    if _SESSION_FACTORY is None:
        _SESSION_FACTORY = sessionmaker(bind=get_engine(), expire_on_commit=False, future=True)
    return _SESSION_FACTORY


@contextmanager
def get_session() -> Iterator[Session]:
    """Provide a transactional scope around a series of operations."""

    session = _get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def run_dataframe(query_text: str, params: dict | None = None) -> pd.DataFrame:
    """Fallback helper for simple text queries."""

    with get_engine().connect() as connection:
        result = connection.execute(text(query_text), params or {})
        rows = result.mappings().all()
    return pd.DataFrame(rows)

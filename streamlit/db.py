"""Database helpers for Streamlit queries."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator, Sequence

import mysql.connector
import pandas as pd
from mysql.connector import pooling

from config import AppSettings, get_settings

_CONNECTION_POOL: pooling.MySQLConnectionPool | None = None


def _ensure_pool(settings: AppSettings | None = None) -> None:
    """Initialize a reusable connection pool if it does not already exist."""

    global _CONNECTION_POOL
    if _CONNECTION_POOL is not None:
        return

    app_settings = settings or get_settings()
    db = app_settings.database
    _CONNECTION_POOL = pooling.MySQLConnectionPool(
        pool_name="streamlit_pool",
        pool_size=5,
        host=db.host,
        port=db.port,
        user=db.user,
        password=db.password,
        database=db.name,
        charset="utf8mb4",
        autocommit=True,
    )


@contextmanager
def get_connection(settings: AppSettings | None = None) -> Iterator[mysql.connector.MySQLConnection]:
    """Context manager that yields a pooled MySQL connection."""

    _ensure_pool(settings)
    assert _CONNECTION_POOL is not None  # for mypy/static checkers
    connection = _CONNECTION_POOL.get_connection()
    try:
        yield connection
    finally:
        connection.close()


def run_query(sql: str, params: Sequence[Any] | None = None) -> pd.DataFrame:
    """Execute a SQL query and return a DataFrame."""

    with get_connection() as connection:
        return pd.read_sql(sql, connection, params=params)


def run_scalar(sql: str, params: Sequence[Any] | None = None) -> Any:
    """Execute a scalar query (first column of the first row)."""

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(sql, params or ())
        row = cursor.fetchone()
        cursor.close()
        return None if row is None else row[0]


def execute(sql: str, params: Sequence[Any] | None = None) -> int:
    """Execute a data-modifying statement and return the last inserted row id."""

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(sql, params or ())
        last_row_id = cursor.lastrowid
        connection.commit()
        cursor.close()
        return last_row_id

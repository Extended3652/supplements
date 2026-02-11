from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable


SCHEMA_SQL: list[str] = [
    """
    CREATE TABLE IF NOT EXISTS items (
        id TEXT PRIMARY KEY,
        name_display TEXT NOT NULL,
        name_generic TEXT,
        brand TEXT,
        category TEXT NOT NULL CHECK (category IN ('rx','otc','supplement')),
        form TEXT,
        route TEXT,
        notes TEXT,
        status TEXT NOT NULL CHECK (status IN ('active','paused','stopped')),
        start_date TEXT,
        stop_date TEXT,
        prescriber TEXT,
        pharmacy TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS doses (
        id TEXT PRIMARY KEY,
        item_id TEXT NOT NULL,
        amount REAL,
        unit TEXT,
        time_am INTEGER NOT NULL DEFAULT 0,
        time_midday INTEGER NOT NULL DEFAULT 0,
        time_pm INTEGER NOT NULL DEFAULT 0,
        with_food INTEGER,
        instructions TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS history (
        id TEXT PRIMARY KEY,
        ts TEXT NOT NULL,
        item_id TEXT NOT NULL,
        action TEXT NOT NULL CHECK (action IN ('create','update','status_change')),
        field TEXT,
        old_value TEXT,
        new_value TEXT,
        note TEXT,
        FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_items_status ON items(status);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_items_category ON items(category);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_history_item_ts ON history(item_id, ts);
    """,
]


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    for stmt in SCHEMA_SQL:
        conn.execute(stmt)
    conn.commit()


def exec_many(conn: sqlite3.Connection, statements: Iterable[str]) -> None:
    for stmt in statements:
        conn.execute(stmt)
    conn.commit()

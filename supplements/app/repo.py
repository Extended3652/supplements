from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from .models import Dose, HistoryEvent, Item


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def list_items(conn: sqlite3.Connection, status: str) -> list[tuple[Item, Optional[Dose]]]:
    rows = conn.execute(
        """
        SELECT
            i.*,
            d.id AS d_id, d.item_id AS d_item_id, d.amount AS d_amount, d.unit AS d_unit,
            d.time_am AS d_time_am, d.time_midday AS d_time_midday, d.time_pm AS d_time_pm,
            d.with_food AS d_with_food, d.instructions AS d_instructions,
            d.created_at AS d_created_at, d.updated_at AS d_updated_at
        FROM items i
        LEFT JOIN doses d ON d.item_id = i.id
        WHERE i.status = ?
        ORDER BY
            CASE i.category WHEN 'rx' THEN 1 WHEN 'otc' THEN 2 ELSE 3 END,
            lower(i.name_display) ASC
        """,
        (status,),
    ).fetchall()

    out: list[tuple[Item, Optional[Dose]]] = []
    for r in rows:
        item = Item(
            id=r["id"],
            name_display=r["name_display"],
            name_generic=r["name_generic"],
            brand=r["brand"],
            category=r["category"],
            form=r["form"],
            route=r["route"],
            notes=r["notes"],
            status=r["status"],
            start_date=r["start_date"],
            stop_date=r["stop_date"],
            prescriber=r["prescriber"],
            pharmacy=r["pharmacy"],
            created_at=r["created_at"],
            updated_at=r["updated_at"],
        )

        dose: Optional[Dose] = None
        if r["d_id"] is not None:
            dose = Dose(
                id=r["d_id"],
                item_id=r["d_item_id"],
                amount=r["d_amount"],
                unit=r["d_unit"],
                time_am=int(r["d_time_am"] or 0),
                time_midday=int(r["d_time_midday"] or 0),
                time_pm=int(r["d_time_pm"] or 0),
                with_food=r["d_with_food"],
                instructions=r["d_instructions"],
                created_at=r["d_created_at"],
                updated_at=r["d_updated_at"],
            )

        out.append((item, dose))

    return out


def create_item_with_dose(
    conn: sqlite3.Connection,
    *,
    name_display: str,
    category: str,
    name_generic: Optional[str] = None,
    brand: Optional[str] = None,
    form: Optional[str] = None,
    route: Optional[str] = None,
    notes: Optional[str] = None,
    amount: Optional[float] = None,
    unit: Optional[str] = None,
    time_am: bool = False,
    time_midday: bool = False,
    time_pm: bool = False,
    with_food: Optional[bool] = None,
    instructions: Optional[str] = None,
) -> str:
    item_id = str(uuid4())
    dose_id = str(uuid4())
    now = _now_iso()

    conn.execute(
        """
        INSERT INTO items (
            id, name_display, name_generic, brand, category, form, route, notes,
            status, start_date, stop_date, prescriber, pharmacy, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', NULL, NULL, NULL, NULL, ?, ?)
        """,
        (item_id, name_display, name_generic, brand, category, form, route, notes, now, now),
    )

    conn.execute(
        """
        INSERT INTO doses (
            id, item_id, amount, unit, time_am, time_midday, time_pm,
            with_food, instructions, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            dose_id,
            item_id,
            amount,
            unit,
            1 if time_am else 0,
            1 if time_midday else 0,
            1 if time_pm else 0,
            None if with_food is None else (1 if with_food else 0),
            instructions,
            now,
            now,
        ),
    )

    _add_history(conn, item_id=item_id, action="create", note="created item")
    conn.commit()
    return item_id


def update_item_and_dose(
    conn: sqlite3.Connection,
    *,
    item_id: str,
    name_display: str,
    category: str,
    name_generic: Optional[str],
    brand: Optional[str],
    form: Optional[str],
    route: Optional[str],
    notes: Optional[str],
    amount: Optional[float],
    unit: Optional[str],
    time_am: bool,
    time_midday: bool,
    time_pm: bool,
    with_food: Optional[bool],
    instructions: Optional[str],
) -> None:
    now = _now_iso()

    conn.execute(
        """
        UPDATE items
        SET
            name_display = ?,
            name_generic = ?,
            brand = ?,
            category = ?,
            form = ?,
            route = ?,
            notes = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (name_display, name_generic, brand, category, form, route, notes, now, item_id),
    )

    dose_row = conn.execute("SELECT id FROM doses WHERE item_id = ?", (item_id,)).fetchone()
    if dose_row is None:
        dose_id = str(uuid4())
        conn.execute(
            """
            INSERT INTO doses (
                id, item_id, amount, unit, time_am, time_midday, time_pm,
                with_food, instructions, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                dose_id,
                item_id,
                amount,
                unit,
                1 if time_am else 0,
                1 if time_midday else 0,
                1 if time_pm else 0,
                None if with_food is None else (1 if with_food else 0),
                instructions,
                now,
                now,
            ),
        )
    else:
        conn.execute(
            """
            UPDATE doses
            SET
                amount = ?,
                unit = ?,
                time_am = ?,
                time_midday = ?,
                time_pm = ?,
                with_food = ?,
                instructions = ?,
                updated_at = ?
            WHERE item_id = ?
            """,
            (
                amount,
                unit,
                1 if time_am else 0,
                1 if time_midday else 0,
                1 if time_pm else 0,
                None if with_food is None else (1 if with_food else 0),
                instructions,
                now,
                item_id,
            ),
        )

    _add_history(conn, item_id=item_id, action="update", note="updated item")
    conn.commit()


def set_status(conn: sqlite3.Connection, *, item_id: str, status: str) -> None:
    now = _now_iso()
    stop_date = now.split("T")[0] if status == "stopped" else None

    conn.execute(
        """
        UPDATE items
        SET status = ?, stop_date = ?, updated_at = ?
        WHERE id = ?
        """,
        (status, stop_date, now, item_id),
    )

    _add_history(conn, item_id=item_id, action="status_change", note=f"status -> {status}")
    conn.commit()


def get_history(conn: sqlite3.Connection, *, item_id: Optional[str] = None, limit: int = 200) -> list[HistoryEvent]:
    if item_id:
        rows = conn.execute(
            """
            SELECT * FROM history
            WHERE item_id = ?
            ORDER BY ts DESC
            LIMIT ?
            """,
            (item_id, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT * FROM history
            ORDER BY ts DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    out: list[HistoryEvent] = []
    for r in rows:
        out.append(
            HistoryEvent(
                id=r["id"],
                ts=r["ts"],
                item_id=r["item_id"],
                action=r["action"],
                field=r["field"],
                old_value=r["old_value"],
                new_value=r["new_value"],
                note=r["note"],
            )
        )
    return out


def _add_history(
    conn: sqlite3.Connection,
    *,
    item_id: str,
    action: str,
    field: Optional[str] = None,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    note: Optional[str] = None,
) -> None:
    conn.execute(
        """
        INSERT INTO history (id, ts, item_id, action, field, old_value, new_value, note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (str(uuid4()), _now_iso(), item_id, action, field, old_value, new_value, note),
    )

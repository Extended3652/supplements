from __future__ import annotations

import sqlite3

from textual.app import App

from ..config import get_config
from ..db import connect, init_db
from ..repo import (
    create_item_with_dose,
    list_items,
    set_status,
    update_item_and_dose,
)
from .screens.edit_item import EditItemScreen, SaveRequested
from .screens.list_view import EditRequested, ListView, StatusRequested


class SupplementsTUI(App):
    CSS = """
    #title { padding: 1 2; }
    #buttons { padding: 1 2; height: auto; }
    #modal_title { padding: 1 2; }
    #error { padding: 0 2; color: red; }
    """

    BINDINGS = [
        ("1", "show_active", "Active"),
        ("2", "show_paused", "Paused"),
        ("3", "show_stopped", "Stopped"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.cfg = get_config()
        self.conn: sqlite3.Connection = connect(self.cfg.db_path)
        init_db(self.conn)

        self.screens_by_name = {
            "active": ListView("Active (1/2/3 to switch)", "active"),
            "paused": ListView("Paused (1/2/3 to switch)", "paused"),
            "stopped": ListView("Stopped (1/2/3 to switch)", "stopped"),
        }

    def on_mount(self) -> None:
        for name, screen in self.screens_by_name.items():
            self.install_screen(screen, name=name)

        self.push_screen("active")
        self.call_after_refresh(lambda: self._refresh_screen("active"))

    def _refresh_screen(self, name: str) -> None:
        screen = self.screens_by_name[name]
        rows = list_items(self.conn, screen.status)

        formatted = []
        for item, dose in rows:
            when = ""
            dose_str = ""

            if dose:
                parts = []
                if dose.time_am:
                    parts.append("AM")
                if dose.time_midday:
                    parts.append("Midday")
                if dose.time_pm:
                    parts.append("PM")
                when = ", ".join(parts)

                if dose.amount is not None and dose.unit:
                    dose_str = f"{dose.amount:g} {dose.unit}"
                elif dose.amount is not None:
                    dose_str = f"{dose.amount:g}"
                elif dose.unit:
                    dose_str = dose.unit

            formatted.append(
                {
                    "id": item.id,
                    "name": item.name_display,
                    "category": item.category,
                    "dose": dose_str,
                    "when": when,
                    "brand": item.brand or "",
                    "notes": item.notes or "",
                }
            )

        screen.load_rows(formatted)

    def _switch_and_refresh(self, name: str) -> None:
        self.switch_screen(name)
        self.call_after_refresh(lambda: self._refresh_screen(name))

    def action_show_active(self) -> None:
        self._switch_and_refresh("active")

    def action_show_paused(self) -> None:
        self._switch_and_refresh("paused")

    def action_show_stopped(self) -> None:
        self._switch_and_refresh("stopped")

    async def on_edit_requested(self, message: EditRequested) -> None:
        item_id = message.item_id
        initial = {}

        if item_id:
            for status in ["active", "paused", "stopped"]:
                rows = list_items(self.conn, status)
                for item, dose in rows:
                    if item.id == item_id:
                        initial = {
                            "name_display": item.name_display,
                            "category": item.category,
                            "brand": item.brand,
                            "name_generic": item.name_generic,
                            "form": item.form,
                            "route": item.route,
                            "notes": item.notes,
                            "amount": None if not dose else dose.amount,
                            "unit": None if not dose else dose.unit,
                            "time_am": False if not dose else bool(dose.time_am),
                            "time_midday": False if not dose else bool(dose.time_midday),
                            "time_pm": False if not dose else bool(dose.time_pm),
                        }
                        break

        await self.push_screen(EditItemScreen(item_id, initial))

    async def on_save_requested(self, message: SaveRequested) -> None:
        item_id = message.item_id
        p = message.payload

        if item_id is None:
            create_item_with_dose(
                self.conn,
                name_display=p["name_display"],
                category=p["category"],
                name_generic=p["name_generic"],
                brand=p["brand"],
                form=p["form"],
                route=p["route"],
                notes=p["notes"],
                amount=p["amount"],
                unit=p["unit"],
                time_am=p["time_am"],
                time_midday=p["time_midday"],
                time_pm=p["time_pm"],
                with_food=None,
                instructions=None,
            )
        else:
            update_item_and_dose(
                self.conn,
                item_id=item_id,
                name_display=p["name_display"],
                category=p["category"],
                name_generic=p["name_generic"],
                brand=p["brand"],
                form=p["form"],
                route=p["route"],
                notes=p["notes"],
                amount=p["amount"],
                unit=p["unit"],
                time_am=p["time_am"],
                time_midday=p["time_midday"],
                time_pm=p["time_pm"],
                with_food=None,
                instructions=None,
            )

        # Refresh the currently visible status tab
        current = self.screen
        for name, scr in self.screens_by_name.items():
            if scr is current:
                self.call_after_refresh(lambda n=name: self._refresh_screen(n))
                break

    async def on_status_requested(self, message: StatusRequested) -> None:
        set_status(self.conn, item_id=message.item_id, status=message.new_status)

        current = self.screen
        for name, scr in self.screens_by_name.items():
            if scr is current:
                self.call_after_refresh(lambda n=name: self._refresh_screen(n))
                break

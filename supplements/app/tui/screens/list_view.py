from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Button, DataTable, Static
from textual.css.query import NoMatches


class EditRequested(Message, bubble=True):
    def __init__(self, item_id: str | None):
        super().__init__()
        self.item_id = item_id


class StatusRequested(Message, bubble=True):
    def __init__(self, item_id: str, new_status: str):
        super().__init__()
        self.item_id = item_id
        self.new_status = new_status


class ListView(Screen):
    BINDINGS = [
        ("a", "add", "Add"),
        ("enter", "edit", "Edit"),
        ("p", "pause_resume", "Pause/Resume"),
        ("s", "stop", "Stop"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, title: str, status: str):
        super().__init__()
        self.title = title
        self.status = status
        self._row_item_ids: list[str] = []
        self._pending_rows: list[dict] | None = None

    def compose(self) -> ComposeResult:
        yield Static(f"{self.title}", id="title")
        yield DataTable(id="table")
        with Horizontal(id="buttons"):
            yield Button("Add", id="btn_add")
            yield Button("Edit", id="btn_edit")
            yield Button("Pause/Resume", id="btn_pause")
            yield Button("Stop", id="btn_stop")

    def on_mount(self) -> None:
        table = self.query_one("#table", DataTable)
        table.add_columns("Name", "Category", "Dose", "When", "Brand", "Notes")
        table.cursor_type = "row"

        if self._pending_rows is not None:
            rows = self._pending_rows
            self._pending_rows = None
            self.load_rows(rows)

    def load_rows(self, rows: list[dict]) -> None:
        try:
            table = self.query_one("#table", DataTable)
        except NoMatches:
            self._pending_rows = rows
            return

        table.clear()
        self._row_item_ids = []

        for r in rows:
            self._row_item_ids.append(r["id"])
            table.add_row(
                r["name"],
                r["category"],
                r["dose"],
                r["when"],
                r["brand"],
                r["notes"],
            )

        if table.row_count > 0:
            table.cursor_coordinate = (0, 0)

    def _selected_item_id(self) -> str | None:
        table = self.query_one("#table", DataTable)
        if table.row_count == 0:
            return None
        row = table.cursor_row
        if row is None:
            return None
        if row < 0 or row >= len(self._row_item_ids):
            return None
        return self._row_item_ids[row]

    def action_add(self) -> None:
        # Post directly to app for reliability.
        self.app.post_message(EditRequested(None))

    def action_edit(self) -> None:
        item_id = self._selected_item_id()
        if item_id:
            self.app.post_message(EditRequested(item_id))

    def action_pause_resume(self) -> None:
        item_id = self._selected_item_id()
        if not item_id:
            return
        new_status = "paused" if self.status == "active" else "active"
        self.app.post_message(StatusRequested(item_id, new_status))

    def action_stop(self) -> None:
        item_id = self._selected_item_id()
        if item_id:
            self.app.post_message(StatusRequested(item_id, "stopped"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_add":
            self.action_add()
        elif event.button.id == "btn_edit":
            self.action_edit()
        elif event.button.id == "btn_pause":
            self.action_pause_resume()
        elif event.button.id == "btn_stop":
            self.action_stop()

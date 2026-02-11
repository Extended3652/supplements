from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Grid
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Input, Label, Select, Static


class SaveRequested(Message, bubble=True):
    def __init__(self, item_id: str | None, payload: dict):
        super().__init__()
        self.item_id = item_id
        self.payload = payload


class EditItemScreen(ModalScreen):
    def __init__(self, item_id: str | None, initial: dict):
        super().__init__()
        self.item_id = item_id
        self.initial = initial

    def compose(self) -> ComposeResult:
        yield Static("Add/Edit Item", id="modal_title")

        with Grid(id="form"):
            yield Label("Name")
            yield Input(value=self.initial.get("name_display", ""), id="name_display")

            yield Label("Category")
            yield Select(
                [
                    ("rx", "rx"),
                    ("otc", "otc"),
                    ("supplement", "supplement"),
                ],
                value=self.initial.get("category", "supplement"),
                id="category",
            )

            yield Label("Brand")
            yield Input(value=self.initial.get("brand", "") or "", id="brand")

            yield Label("Generic name")
            yield Input(value=self.initial.get("name_generic", "") or "", id="name_generic")

            yield Label("Form")
            yield Input(value=self.initial.get("form", "") or "", id="form")

            yield Label("Route")
            yield Input(value=self.initial.get("route", "") or "", id="route")

            yield Label("Dose amount")
            yield Input(value=self.initial.get("amount", "") or "", id="amount", placeholder="ex: 10 or 600")

            yield Label("Dose unit")
            yield Input(value=self.initial.get("unit", "") or "", id="unit", placeholder="mg, mcg, IU, g, caps, tabs")

            yield Label("When")
            yield Checkbox("AM", value=bool(self.initial.get("time_am", False)), id="time_am")
            yield Checkbox("Midday", value=bool(self.initial.get("time_midday", False)), id="time_midday")
            yield Checkbox("PM", value=bool(self.initial.get("time_pm", False)), id="time_pm")

            yield Label("Notes")
            yield Input(value=self.initial.get("notes", "") or "", id="notes")

        yield Static("", id="error")

        yield Button("Save", id="save", variant="primary")
        yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#form", Grid).styles.grid_size_columns = 2
        self.query_one("#form", Grid).styles.grid_size_rows = "auto"
        self.query_one("#name_display", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(None)
            return

        if event.button.id != "save":
            return

        name_display = self.query_one("#name_display", Input).value.strip()
        if not name_display:
            self.query_one("#error", Static).update("Name is required.")
            return

        category = self.query_one("#category", Select).value or "supplement"

        amount_raw = self.query_one("#amount", Input).value.strip()
        amount = None
        if amount_raw:
            try:
                amount = float(amount_raw)
            except ValueError:
                self.query_one("#error", Static).update("Dose amount must be a number.")
                return

        payload = {
            "name_display": name_display,
            "category": category,
            "brand": self.query_one("#brand", Input).value.strip() or None,
            "name_generic": self.query_one("#name_generic", Input).value.strip() or None,
            "form": self.query_one("#form", Input).value.strip() or None,
            "route": self.query_one("#route", Input).value.strip() or None,
            "notes": self.query_one("#notes", Input).value.strip() or None,
            "amount": amount,
            "unit": self.query_one("#unit", Input).value.strip() or None,
            "time_am": self.query_one("#time_am", Checkbox).value,
            "time_midday": self.query_one("#time_midday", Checkbox).value,
            "time_pm": self.query_one("#time_pm", Checkbox).value,
            "with_food": None,
            "instructions": None,
        }

        self.post_message(SaveRequested(self.item_id, payload))
        self.dismiss(None)

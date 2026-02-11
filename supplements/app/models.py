from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Item:
    id: str
    name_display: str
    name_generic: Optional[str]
    brand: Optional[str]
    category: str  # rx | otc | supplement
    form: Optional[str]
    route: Optional[str]
    notes: Optional[str]
    status: str  # active | paused | stopped
    start_date: Optional[str]
    stop_date: Optional[str]
    prescriber: Optional[str]
    pharmacy: Optional[str]
    created_at: str
    updated_at: str


@dataclass
class Dose:
    id: str
    item_id: str
    amount: Optional[float]
    unit: Optional[str]
    time_am: int
    time_midday: int
    time_pm: int
    with_food: Optional[int]
    instructions: Optional[str]
    created_at: str
    updated_at: str


@dataclass
class HistoryEvent:
    id: str
    ts: str
    item_id: str
    action: str
    field: Optional[str]
    old_value: Optional[str]
    new_value: Optional[str]
    note: Optional[str]

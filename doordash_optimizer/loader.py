from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from doordash_optimizer.models import Deal, MenuItem, Restaurant


def load_restaurants(path: str | Path) -> list[Restaurant]:
    data = json.loads(Path(path).read_text())
    return [_parse_restaurant(raw) for raw in data["restaurants"]]


def _parse_restaurant(raw: dict[str, Any]) -> Restaurant:
    menu = [
        MenuItem(
            id=item["id"],
            restaurant_id=raw["id"],
            name=item["name"],
            price_cents=item["price_cents"],
            calories=item["calories"],
            max_qty=item["max_qty"],
            tags=tuple(item.get("tags", ())),
        )
        for item in raw["menu"]
    ]
    deals = [Deal(**deal) for deal in raw.get("deals", [])]
    return Restaurant(
        id=raw["id"],
        name=raw["name"],
        menu=menu,
        deals=deals,
        delivery_fee_cents=raw.get("delivery_fee_cents", 0),
        service_fee_rate=raw.get("service_fee_rate", 0.0),
        tax_rate=raw.get("tax_rate", 0.0),
        tip_rate=raw.get("tip_rate", 0.0),
        small_order_fee_cents=raw.get("small_order_fee_cents", 0),
        small_order_threshold_cents=raw.get("small_order_threshold_cents", 0),
    )

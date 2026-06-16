from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

from doordash_optimizer.models import Deal, MenuItem, Restaurant


DEFAULT_MENU_PATH_TEMPLATE = "/restaurants/{restaurant_id}/menu"


@dataclass(frozen=True)
class FoodSparkConfig:
    api_key: str
    base_url: str
    menu_path_template: str = DEFAULT_MENU_PATH_TEMPLATE
    auth_header: str = "Authorization"
    auth_prefix: str = "Bearer"

    @classmethod
    def from_env(cls) -> "FoodSparkConfig":
        missing = [
            name
            for name in ("FOODSPARK_API_KEY", "FOODSPARK_API_BASE_URL")
            if not os.environ.get(name)
        ]
        if missing:
            raise RuntimeError(
                "Missing FoodSpark configuration: "
                + ", ".join(missing)
                + ". Export your FoodSpark API key and tenant-specific base URL."
            )
        return cls(
            api_key=os.environ["FOODSPARK_API_KEY"],
            base_url=os.environ["FOODSPARK_API_BASE_URL"],
            menu_path_template=os.environ.get(
                "FOODSPARK_MENU_PATH_TEMPLATE", DEFAULT_MENU_PATH_TEMPLATE
            ),
            auth_header=os.environ.get("FOODSPARK_AUTH_HEADER", "Authorization"),
            auth_prefix=os.environ.get("FOODSPARK_AUTH_PREFIX", "Bearer"),
        )


class FoodSparkClient:
    def __init__(self, config: FoodSparkConfig, *, timeout_seconds: int = 30) -> None:
        self.config = config
        self.timeout_seconds = timeout_seconds

    @classmethod
    def from_env(cls) -> "FoodSparkClient":
        return cls(FoodSparkConfig.from_env())

    def get_restaurant_menu(self, restaurant_id: str) -> dict[str, Any]:
        escaped_id = quote(restaurant_id, safe="")
        path = self.config.menu_path_template.format(restaurant_id=escaped_id)
        return self._get_json(path)

    def _get_json(self, path: str) -> dict[str, Any]:
        url = self.config.base_url.rstrip("/") + "/" + path.lstrip("/")
        request = Request(
            url,
            headers={
                self.config.auth_header: _auth_value(
                    self.config.auth_prefix, self.config.api_key
                ),
                "Accept": "application/json",
                "User-Agent": "doordash-optimizer/0.1",
            },
            method="GET",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"FoodSpark API request failed with HTTP {error.code}: {body}"
            ) from error


def load_restaurants_from_foodspark_api(
    restaurant_ids: list[str],
    *,
    client: FoodSparkClient | None = None,
    max_qty: int = 5,
    delivery_fee_cents: int = 0,
    service_fee_rate: float = 0.0,
    tax_rate: float = 0.0,
    tip_rate: float = 0.0,
    small_order_fee_cents: int = 0,
    small_order_threshold_cents: int = 0,
) -> list[Restaurant]:
    api_client = client or FoodSparkClient.from_env()
    restaurants = []
    for restaurant_id in restaurant_ids:
        payload = api_client.get_restaurant_menu(restaurant_id)
        restaurants.append(
            restaurant_from_foodspark_payload(
                payload,
                fallback_id=restaurant_id,
                max_qty=max_qty,
                delivery_fee_cents=delivery_fee_cents,
                service_fee_rate=service_fee_rate,
                tax_rate=tax_rate,
                tip_rate=tip_rate,
                small_order_fee_cents=small_order_fee_cents,
                small_order_threshold_cents=small_order_threshold_cents,
            )
        )
    return restaurants


def restaurant_from_foodspark_payload(
    payload: dict[str, Any],
    *,
    fallback_id: str = "restaurant",
    max_qty: int = 5,
    delivery_fee_cents: int = 0,
    service_fee_rate: float = 0.0,
    tax_rate: float = 0.0,
    tip_rate: float = 0.0,
    small_order_fee_cents: int = 0,
    small_order_threshold_cents: int = 0,
) -> Restaurant:
    restaurant_blob = _first_mapping(
        payload,
        "restaurant",
        "store",
        "merchant",
        default=payload,
    )
    restaurant_id = str(
        _first_value(
            restaurant_blob,
            "id",
            "restaurant_id",
            "store_id",
            "merchant_supplied_id",
            default=fallback_id,
        )
    )
    name = str(
        _first_value(
            restaurant_blob,
            "name",
            "restaurant_name",
            "store_name",
            "merchant_name",
            default=restaurant_id,
        )
    )

    raw_items = _extract_items(payload)
    menu = [
        item
        for raw_item in raw_items
        if (
            item := _parse_foodspark_item(
                raw_item,
                restaurant_id=restaurant_id,
                max_qty=max_qty,
            )
        )
        is not None
    ]

    return Restaurant(
        id=restaurant_id,
        name=name,
        menu=menu,
        deals=_parse_foodspark_deals(payload),
        delivery_fee_cents=delivery_fee_cents,
        service_fee_rate=service_fee_rate,
        tax_rate=tax_rate,
        tip_rate=tip_rate,
        small_order_fee_cents=small_order_fee_cents,
        small_order_threshold_cents=small_order_threshold_cents,
    )


def _parse_foodspark_item(
    raw_item: dict[str, Any],
    *,
    restaurant_id: str,
    max_qty: int,
) -> MenuItem | None:
    if raw_item.get("available") is False or raw_item.get("active") is False:
        return None
    item_id = _first_value(raw_item, "id", "item_id", "menu_item_id", "sku")
    name = _first_value(raw_item, "name", "item_name", "title")
    price = _price_cents(raw_item)
    if item_id is None or name is None or price is None:
        return None

    tags = _tags(raw_item)
    item_max_qty = _first_value(raw_item, "max_qty", "max_quantity", default=max_qty)
    return MenuItem(
        id=str(item_id),
        restaurant_id=restaurant_id,
        name=str(name),
        price_cents=price,
        calories=_calories(raw_item),
        max_qty=int(item_max_qty),
        tags=tuple(tags),
    )


def _parse_foodspark_deals(payload: dict[str, Any]) -> list[Deal]:
    raw_deals = _first_list(payload, "deals", "offers", "promotions", "coupons")
    deals = []
    for raw_deal in raw_deals:
        deal_type = raw_deal.get("type") or raw_deal.get("deal_type")
        if deal_type not in {
            "buy_x_get_y",
            "threshold_percent_off",
            "threshold_fixed_off",
            "free_item_over_threshold",
            "combo_bundle",
        }:
            continue
        deals.append(
            Deal(
                id=str(_first_value(raw_deal, "id", "deal_id", "offer_id")),
                type=str(deal_type),
                description=str(raw_deal.get("description") or raw_deal.get("title") or ""),
                item_id=_optional_str(_first_value(raw_deal, "item_id", "menu_item_id")),
                buy_qty=_optional_int(_first_value(raw_deal, "buy_qty", "buy_quantity")),
                free_qty=_optional_int(_first_value(raw_deal, "free_qty", "free_quantity")),
                threshold_cents=_optional_price_cents(
                    _first_value(raw_deal, "threshold_cents", "threshold", "minimum_spend")
                ),
                percent_off=_optional_float(
                    _first_value(raw_deal, "percent_off", "discount_percent")
                ),
                fixed_off_cents=_optional_price_cents(
                    _first_value(raw_deal, "fixed_off_cents", "discount_amount")
                ),
                free_item_id=_optional_str(_first_value(raw_deal, "free_item_id")),
                combo_items=raw_deal.get("combo_items"),
                combo_price_cents=_optional_price_cents(
                    _first_value(raw_deal, "combo_price_cents", "combo_price")
                ),
                stack_group=_optional_str(_first_value(raw_deal, "stack_group")),
                stackable=bool(raw_deal.get("stackable", True)),
            )
        )
    return deals


def _extract_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    direct = _first_list(payload, "items", "menu_items", "products")
    if direct:
        return direct

    menu = _first_mapping(payload, "menu", default={})
    direct = _first_list(menu, "items", "menu_items", "products")
    if direct:
        return direct

    items: list[dict[str, Any]] = []
    for collection_name in ("categories", "sections"):
        for category in _first_list(menu, collection_name):
            category_name = category.get("name") or category.get("title")
            for raw_item in _first_list(category, "items", "menu_items", "products"):
                item = dict(raw_item)
                if category_name and "category" not in item:
                    item["category"] = category_name
                items.append(item)
    return items


def _price_cents(raw_item: dict[str, Any]) -> int | None:
    cents = _first_value(raw_item, "price_cents", "base_price_cents")
    if cents is not None:
        return int(cents)
    price = _first_value(raw_item, "price", "base_price", "amount")
    if price is None:
        return None
    if isinstance(price, dict):
        return _optional_price_cents(
            _first_value(price, "cents", "amount_cents", "amount", "value")
        )
    if isinstance(price, str):
        cleaned = price.replace("$", "").strip()
        return round(float(cleaned) * 100)
    if isinstance(price, float):
        return round(price * 100)
    return int(price)


def _calories(raw_item: dict[str, Any]) -> int:
    nutrition = _first_mapping(raw_item, "nutrition", "nutritional_info", default={})
    value = _first_value(
        raw_item,
        "calories",
        "kcal",
        default=_first_value(nutrition, "calories", "kcal", "calorie_count", default=0),
    )
    if isinstance(value, dict):
        value = _first_value(value, "value", "high", "higher_range", "low", "lower_range")
    return int(float(value or 0))


def _tags(raw_item: dict[str, Any]) -> list[str]:
    tags = []
    category = raw_item.get("category")
    if category:
        tags.append(str(category))
    for key in ("tags", "categories", "dietary_tags"):
        value = raw_item.get(key)
        if isinstance(value, list):
            tags.extend(str(tag) for tag in value)
        elif isinstance(value, str):
            tags.append(value)
    return tags


def _first_mapping(
    source: dict[str, Any], *keys: str, default: dict[str, Any] | None = None
) -> dict[str, Any]:
    for key in keys:
        value = source.get(key)
        if isinstance(value, dict):
            return value
    return {} if default is None else default


def _first_list(source: dict[str, Any], *keys: str) -> list[dict[str, Any]]:
    for key in keys:
        value = source.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def _first_value(source: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in source and source[key] is not None:
            return source[key]
    return default


def _optional_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _optional_int(value: Any) -> int | None:
    return None if value is None else int(value)


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    result = float(value)
    return result / 100 if result > 1 else result


def _optional_price_cents(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.replace("$", "").strip()
        return round(float(cleaned) * 100)
    if isinstance(value, float):
        return round(value * 100)
    return int(value)


def _auth_value(prefix: str, api_key: str) -> str:
    if not prefix:
        return api_key
    return f"{prefix} {api_key}"

from __future__ import annotations

from pathlib import Path
import os
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from doordash_optimizer import explain_result, load_restaurants_from_foodspark_api, optimize


def main() -> None:
    restaurant_ids = [
        restaurant_id.strip()
        for restaurant_id in os.environ.get("FOODSPARK_RESTAURANT_IDS", "").split(",")
        if restaurant_id.strip()
    ]
    if not restaurant_ids:
        raise SystemExit(
            "Set FOODSPARK_RESTAURANT_IDS to one or more FoodSpark restaurant IDs. "
            "This demo uses the FoodSpark API, not sample data."
        )

    restaurants = load_restaurants_from_foodspark_api(
        restaurant_ids,
        max_qty=_env_int("FOODSPARK_ITEM_MAX_QTY", 5),
        delivery_fee_cents=_env_int("DEFAULT_DELIVERY_FEE_CENTS", 0),
        service_fee_rate=_env_float("DEFAULT_SERVICE_FEE_RATE", 0.0),
        tax_rate=_env_float("DEFAULT_TAX_RATE", 0.0),
        tip_rate=_env_float("DEFAULT_TIP_RATE", 0.0),
        small_order_fee_cents=_env_int("DEFAULT_SMALL_ORDER_FEE_CENTS", 0),
        small_order_threshold_cents=_env_int("DEFAULT_SMALL_ORDER_THRESHOLD_CENTS", 0),
    )
    result = optimize(
        restaurants,
        budget_cents=_env_int("BUDGET_CENTS", 3500),
        max_restaurants=_env_int("MAX_RESTAURANTS", 2),
    )
    print(explain_result(result))


def _env_int(name: str, default: int) -> int:
    return int(os.environ.get(name, default))


def _env_float(name: str, default: float) -> float:
    return float(os.environ.get(name, default))


if __name__ == "__main__":
    main()

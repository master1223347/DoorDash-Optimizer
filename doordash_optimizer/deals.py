from __future__ import annotations

from itertools import combinations

from doordash_optimizer.fees import round_cents
from doordash_optimizer.models import Deal, MenuItem

ITEM_LEVEL_DEALS = {"buy_x_get_y"}
RESTAURANT_LEVEL_DEALS = {
    "threshold_percent_off",
    "threshold_fixed_off",
    "free_item_over_threshold",
}
DEAL_APPLICATION_ORDER = {
    "threshold_percent_off": 10,
    "threshold_fixed_off": 20,
    "free_item_over_threshold": 30,
}


def paid_units_for_buy_x_get_y(quantity: int, buy_qty: int, free_qty: int) -> int:
    if quantity < 0:
        raise ValueError("quantity must be non-negative")
    if buy_qty <= 0 or free_qty < 0:
        raise ValueError("buy_qty must be positive and free_qty must be non-negative")
    ladder_size = buy_qty + free_qty
    full_ladders, remainder = divmod(quantity, ladder_size)
    return full_ladders * buy_qty + min(remainder, buy_qty)


def effective_item_option(
    item: MenuItem, quantity: int, deals: list[Deal]
) -> tuple[int, int, list[str]]:
    """Return listed subtotal, charged subtotal, and item-level deal ids."""
    listed_subtotal = item.price_cents * quantity
    if quantity == 0:
        return 0, 0, []

    best_cost = listed_subtotal
    best_deals: list[str] = []
    for deal in deals:
        if deal.type != "buy_x_get_y" or deal.item_id != item.id:
            continue
        if deal.buy_qty is None or deal.free_qty is None:
            raise ValueError(f"Deal {deal.id} is missing buy/free quantities")
        paid_units = paid_units_for_buy_x_get_y(quantity, deal.buy_qty, deal.free_qty)
        cost = paid_units * item.price_cents
        if cost < best_cost:
            best_cost = cost
            best_deals = [deal.id]
    return listed_subtotal, best_cost, best_deals


def legal_deal_scenarios(deals: list[Deal]) -> list[tuple[Deal, ...]]:
    restaurant_deals = [deal for deal in deals if deal.type in RESTAURANT_LEVEL_DEALS]
    scenarios: list[tuple[Deal, ...]] = []
    for size in range(len(restaurant_deals) + 1):
        for subset in combinations(restaurant_deals, size):
            if _is_legal_subset(subset):
                scenarios.append(tuple(sorted(subset, key=_deal_sort_key)))
    return scenarios


def _is_legal_subset(subset: tuple[Deal, ...]) -> bool:
    grouped: dict[str, int] = {}
    for deal in subset:
        if deal.stack_group:
            grouped[deal.stack_group] = grouped.get(deal.stack_group, 0) + 1
            if grouped[deal.stack_group] > 1:
                return False
        if not deal.stackable and len(subset) > 1:
            return False
    return True


def _deal_sort_key(deal: Deal) -> tuple[int, str]:
    return DEAL_APPLICATION_ORDER.get(deal.type, 100), deal.id


def apply_restaurant_deal(
    deal: Deal,
    *,
    pre_discount_subtotal_cents: int,
    discounted_subtotal_cents: int,
    calories: int,
    items: dict[str, int],
    item_names: dict[str, str],
    menu_by_id: dict[str, MenuItem],
) -> tuple[int, int, dict[str, int], dict[str, str], bool]:
    threshold = deal.threshold_cents or 0
    if pre_discount_subtotal_cents < threshold:
        return discounted_subtotal_cents, calories, items, item_names, False

    if deal.type == "threshold_percent_off":
        if deal.percent_off is None:
            raise ValueError(f"Deal {deal.id} is missing percent_off")
        discount = round_cents(discounted_subtotal_cents * deal.percent_off)
        return max(0, discounted_subtotal_cents - discount), calories, items, item_names, True

    if deal.type == "threshold_fixed_off":
        fixed_off = deal.fixed_off_cents or 0
        return max(0, discounted_subtotal_cents - fixed_off), calories, items, item_names, True

    if deal.type == "free_item_over_threshold":
        if not deal.free_item_id or deal.free_item_id not in menu_by_id:
            raise ValueError(f"Deal {deal.id} has an unknown free_item_id")
        free_item = menu_by_id[deal.free_item_id]
        next_items = dict(items)
        next_item_names = dict(item_names)
        next_items[free_item.id] = next_items.get(free_item.id, 0) + 1
        next_item_names[free_item.id] = free_item.name
        return (
            discounted_subtotal_cents,
            calories + free_item.calories,
            next_items,
            next_item_names,
            True,
        )

    return discounted_subtotal_cents, calories, items, item_names, False

from __future__ import annotations

from dataclasses import dataclass

from doordash_optimizer.deals import (
    apply_restaurant_deal,
    effective_item_option,
    legal_deal_scenarios,
)
from doordash_optimizer.fees import final_cost_cents
from doordash_optimizer.models import Bundle, Deal, MenuItem, OptimizationResult, Restaurant


@dataclass(frozen=True)
class BasketState:
    pre_discount_subtotal_cents: int
    discounted_subtotal_cents: int
    calories: int
    items: dict[str, int]
    item_names: dict[str, str]
    deals_used: list[str]


@dataclass(frozen=True)
class OptimizationState:
    bundles: list[Bundle]
    total_cost_cents: int
    total_calories: int


def generate_restaurant_frontier(
    restaurant: Restaurant, budget_cents: int | None = None
) -> list[Bundle]:
    states = list(_restaurant_dp(restaurant).values())
    states.extend(_combo_bundle_states(restaurant))

    candidates: list[Bundle] = []
    for state in states:
        if not state.items:
            continue
        candidates.extend(apply_best_legal_deal_scenario(state, restaurant))

    if budget_cents is not None:
        candidates = [bundle for bundle in candidates if bundle.final_cost_cents <= budget_cents]
    return pareto_prune(candidates)


def _restaurant_dp(restaurant: Restaurant) -> dict[int, BasketState]:
    dp: dict[int, BasketState] = {
        0: BasketState(0, 0, 0, {}, {}, []),
    }
    for item in restaurant.menu:
        options = _item_options(item, restaurant.deals)
        next_dp = dict(dp)
        for state in dp.values():
            for option in options:
                if option.pre_discount_subtotal_cents == 0:
                    continue
                candidate = _merge_item_option(state, option)
                current = next_dp.get(candidate.pre_discount_subtotal_cents)
                if current is None or _basket_state_better(candidate, current):
                    next_dp[candidate.pre_discount_subtotal_cents] = candidate
        dp = next_dp
    return dp


def _item_options(item: MenuItem, deals: list[Deal]) -> list[BasketState]:
    options: list[BasketState] = []
    for quantity in range(item.max_qty + 1):
        pre, discounted, deals_used = effective_item_option(item, quantity, deals)
        items = {item.id: quantity} if quantity else {}
        item_names = {item.id: item.name} if quantity else {}
        options.append(
            BasketState(
                pre_discount_subtotal_cents=pre,
                discounted_subtotal_cents=discounted,
                calories=item.calories * quantity,
                items=items,
                item_names=item_names,
                deals_used=deals_used,
            )
        )
    return options


def _merge_item_option(state: BasketState, option: BasketState) -> BasketState:
    items = dict(state.items)
    item_names = dict(state.item_names)
    for item_id, quantity in option.items.items():
        items[item_id] = items.get(item_id, 0) + quantity
    item_names.update(option.item_names)
    deals_used = _dedupe_preserving_order([*state.deals_used, *option.deals_used])
    return BasketState(
        pre_discount_subtotal_cents=(
            state.pre_discount_subtotal_cents + option.pre_discount_subtotal_cents
        ),
        discounted_subtotal_cents=(
            state.discounted_subtotal_cents + option.discounted_subtotal_cents
        ),
        calories=state.calories + option.calories,
        items=items,
        item_names=item_names,
        deals_used=deals_used,
    )


def _basket_state_better(candidate: BasketState, incumbent: BasketState) -> bool:
    return (
        candidate.calories,
        -candidate.discounted_subtotal_cents,
        -sum(candidate.items.values()),
    ) > (
        incumbent.calories,
        -incumbent.discounted_subtotal_cents,
        -sum(incumbent.items.values()),
    )


def _combo_bundle_states(restaurant: Restaurant) -> list[BasketState]:
    menu_by_id = {item.id: item for item in restaurant.menu}
    states: list[BasketState] = []
    for deal in restaurant.deals:
        if deal.type != "combo_bundle":
            continue
        if not deal.combo_items or deal.combo_price_cents is None:
            raise ValueError(f"Combo deal {deal.id} needs combo_items and combo_price_cents")
        items: dict[str, int] = {}
        item_names: dict[str, str] = {}
        pre_discount = 0
        calories = 0
        for item_id, quantity in deal.combo_items.items():
            if item_id not in menu_by_id:
                raise ValueError(f"Combo deal {deal.id} references unknown item {item_id}")
            item = menu_by_id[item_id]
            items[item_id] = items.get(item_id, 0) + quantity
            item_names[item_id] = item.name
            pre_discount += item.price_cents * quantity
            calories += item.calories * quantity
        states.append(
            BasketState(
                pre_discount_subtotal_cents=pre_discount,
                discounted_subtotal_cents=deal.combo_price_cents,
                calories=calories,
                items=items,
                item_names=item_names,
                deals_used=[deal.id],
            )
        )
    return states


def apply_best_legal_deal_scenario(
    basket_state: BasketState, restaurant: Restaurant
) -> list[Bundle]:
    menu_by_id = {item.id: item for item in restaurant.menu}
    bundles: list[Bundle] = []
    for scenario in legal_deal_scenarios(restaurant.deals):
        discounted_subtotal = basket_state.discounted_subtotal_cents
        calories = basket_state.calories
        items = dict(basket_state.items)
        item_names = dict(basket_state.item_names)
        deals_used = list(basket_state.deals_used)

        for deal in scenario:
            discounted_subtotal, calories, items, item_names, applied = apply_restaurant_deal(
                deal,
                pre_discount_subtotal_cents=basket_state.pre_discount_subtotal_cents,
                discounted_subtotal_cents=discounted_subtotal,
                calories=calories,
                items=items,
                item_names=item_names,
                menu_by_id=menu_by_id,
            )
            if applied:
                deals_used.append(deal.id)

        final_cost = final_cost_cents(discounted_subtotal, restaurant)
        bundles.append(
            Bundle(
                restaurant_id=restaurant.id,
                restaurant_name=restaurant.name,
                items=items,
                item_names=item_names,
                pre_discount_subtotal_cents=basket_state.pre_discount_subtotal_cents,
                discounted_subtotal_cents=discounted_subtotal,
                final_cost_cents=final_cost,
                calories=calories,
                deals_used=_dedupe_preserving_order(deals_used),
            )
        )
    return bundles


def pareto_prune(bundles: list[Bundle]) -> list[Bundle]:
    sorted_bundles = sorted(
        bundles,
        key=lambda bundle: (bundle.final_cost_cents, -bundle.calories, bundle.restaurant_name),
    )
    pruned: list[Bundle] = []
    best_calories_seen = -1
    for bundle in sorted_bundles:
        if bundle.calories > best_calories_seen:
            pruned.append(bundle)
            best_calories_seen = bundle.calories
    return pruned


def optimize(
    restaurants: list[Restaurant], budget_cents: int, max_restaurants: int = 1
) -> OptimizationResult:
    if budget_cents < 0:
        raise ValueError("budget_cents must be non-negative")
    if max_restaurants < 0:
        raise ValueError("max_restaurants must be non-negative")

    dp: dict[tuple[int, int], OptimizationState] = {
        (0, 0): OptimizationState([], 0, 0),
    }
    for restaurant in restaurants:
        frontier = generate_restaurant_frontier(restaurant, budget_cents)
        next_dp = dict(dp)
        for (spent, restaurants_used), state in dp.items():
            for bundle in frontier:
                new_spent = spent + bundle.final_cost_cents
                new_restaurants_used = restaurants_used + 1
                if new_spent > budget_cents or new_restaurants_used > max_restaurants:
                    continue
                candidate = OptimizationState(
                    bundles=[*state.bundles, bundle],
                    total_cost_cents=new_spent,
                    total_calories=state.total_calories + bundle.calories,
                )
                key = (new_spent, new_restaurants_used)
                incumbent = next_dp.get(key)
                if incumbent is None or candidate.total_calories > incumbent.total_calories:
                    next_dp[key] = candidate
        dp = next_dp

    best_state = max(
        dp.values(),
        key=lambda state: (
            state.total_calories,
            -state.total_cost_cents,
            -len(state.bundles),
        ),
    )
    return OptimizationResult(
        bundles=best_state.bundles,
        total_cost_cents=best_state.total_cost_cents,
        total_calories=best_state.total_calories,
        budget_cents=budget_cents,
    )


def _dedupe_preserving_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result

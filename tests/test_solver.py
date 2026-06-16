from __future__ import annotations

from itertools import product
from random import Random

from doordash_optimizer.fees import final_cost_cents
from doordash_optimizer.models import Bundle, Deal, MenuItem, Restaurant
from doordash_optimizer.solver import generate_restaurant_frontier, optimize, pareto_prune


def test_threshold_below_and_at_threshold() -> None:
    below_restaurant = Restaurant(
        id="r",
        name="Threshold",
        menu=[MenuItem("a", "r", "A", 900, 100, 1)],
        deals=[
            Deal(
                id="half_over_10",
                type="threshold_percent_off",
                description="50% off $10",
                threshold_cents=1000,
                percent_off=0.5,
            )
        ],
    )
    at_restaurant = Restaurant(
        id="r",
        name="Threshold",
        menu=[MenuItem("a", "r", "A", 1000, 100, 1)],
        deals=below_restaurant.deals,
    )

    below = generate_restaurant_frontier(below_restaurant, 2000)[0]
    at_threshold = generate_restaurant_frontier(at_restaurant, 2000)[0]
    assert below.discounted_subtotal_cents == 900
    assert at_threshold.discounted_subtotal_cents == 500


def test_fee_model_includes_all_components() -> None:
    restaurant = Restaurant(
        id="r",
        name="Fees",
        menu=[],
        delivery_fee_cents=100,
        service_fee_rate=0.1,
        tax_rate=0.08,
        tip_rate=0.2,
        small_order_fee_cents=50,
        small_order_threshold_cents=1000,
    )

    assert final_cost_cents(500, restaurant) == 500 + 100 + 50 + 40 + 100 + 50
    assert final_cost_cents(1000, restaurant) == 1000 + 100 + 100 + 80 + 200


def test_pareto_prune_removes_dominated_and_keeps_non_dominated() -> None:
    bundles = [
        _bundle("a", cost=1000, calories=100),
        _bundle("b", cost=900, calories=100),
        _bundle("c", cost=1100, calories=130),
    ]

    pruned = pareto_prune(bundles)

    assert [bundle.restaurant_id for bundle in pruned] == ["b", "c"]


def test_optimizer_respects_budget_and_max_restaurants() -> None:
    restaurants = [
        _simple_restaurant("r1", price=500, calories=500),
        _simple_restaurant("r2", price=500, calories=600),
    ]

    result = optimize(restaurants, budget_cents=1000, max_restaurants=1)

    assert result.total_cost_cents <= 1000
    assert len(result.bundles) == 1
    assert result.total_calories == 600


def test_bogo_item_can_beat_cheaper_ordinary_item() -> None:
    restaurant = Restaurant(
        id="r",
        name="BOGO",
        menu=[
            MenuItem("burger", "r", "Burger", 1000, 900, 2),
            MenuItem("cheap", "r", "Cheap", 600, 450, 2),
        ],
        deals=[
            Deal(
                id="bogo",
                type="buy_x_get_y",
                description="BOGO burger",
                item_id="burger",
                buy_qty=1,
                free_qty=1,
            )
        ],
    )

    result = optimize([restaurant], budget_cents=1000)

    assert result.total_calories == 1800
    assert result.bundles[0].items == {"burger": 2}


def test_threshold_filler_selected_when_it_improves_outcome() -> None:
    restaurant = Restaurant(
        id="r",
        name="Filler",
        menu=[
            MenuItem("main", "r", "Main", 950, 800, 1),
            MenuItem("filler", "r", "Filler", 50, 10, 1),
        ],
        deals=[
            Deal(
                id="half_over_10",
                type="threshold_percent_off",
                description="50% off $10",
                threshold_cents=1000,
                percent_off=0.5,
            )
        ],
    )

    result = optimize([restaurant], budget_cents=700)

    assert result.total_calories == 810
    assert result.bundles[0].items == {"main": 1, "filler": 1}
    assert result.total_cost_cents == 500


def test_multi_restaurant_selected_only_when_it_beats_single_restaurant() -> None:
    restaurants = [
        _simple_restaurant("r1", price=1000, calories=1000),
        _simple_restaurant("r2", price=900, calories=950),
    ]

    one = optimize(restaurants, budget_cents=1900, max_restaurants=1)
    two = optimize(restaurants, budget_cents=1900, max_restaurants=2)

    assert len(one.bundles) == 1
    assert one.total_calories == 1000
    assert len(two.bundles) == 2
    assert two.total_calories == 1950


def test_free_item_over_threshold_adds_calories_without_cost() -> None:
    restaurant = Restaurant(
        id="r",
        name="Freebie",
        menu=[
            MenuItem("meal", "r", "Meal", 1800, 1000, 1),
            MenuItem("churro", "r", "Churro", 300, 250, 1),
        ],
        deals=[
            Deal(
                id="free_churro_over_18",
                type="free_item_over_threshold",
                description="Free churro over $18",
                threshold_cents=1800,
                free_item_id="churro",
            )
        ],
    )

    result = optimize([restaurant], budget_cents=1800)

    assert result.total_calories == 1250
    assert result.bundles[0].items == {"meal": 1, "churro": 1}


def test_non_stackable_coupon_group_chooses_best_legal_scenario() -> None:
    restaurant = Restaurant(
        id="r",
        name="Coupons",
        menu=[MenuItem("meal", "r", "Meal", 2000, 1000, 1)],
        deals=[
            Deal(
                id="ten_percent",
                type="threshold_percent_off",
                description="10% off",
                threshold_cents=1000,
                percent_off=0.1,
                stack_group="coupon",
            ),
            Deal(
                id="five_off",
                type="threshold_fixed_off",
                description="$5 off",
                threshold_cents=1000,
                fixed_off_cents=500,
                stack_group="coupon",
            ),
        ],
    )

    result = optimize([restaurant], budget_cents=2000)

    assert result.total_cost_cents == 1500
    assert result.bundles[0].deals_used == ["five_off"]


def test_combo_bundle_can_win() -> None:
    restaurant = Restaurant(
        id="r",
        name="Combo",
        menu=[
            MenuItem("pizza", "r", "Pizza", 1000, 1000, 1),
            MenuItem("side", "r", "Side", 500, 400, 1),
        ],
        deals=[
            Deal(
                id="combo",
                type="combo_bundle",
                description="Combo",
                combo_items={"pizza": 1, "side": 1},
                combo_price_cents=1200,
            )
        ],
    )

    result = optimize([restaurant], budget_cents=1200)

    assert result.total_calories == 1400
    assert result.bundles[0].deals_used == ["combo"]


def test_dp_matches_brute_force_for_tiny_random_menus() -> None:
    rng = Random(7)
    for case in range(25):
        item_count = rng.randint(1, 3)
        menu = [
            MenuItem(
                id=f"i{idx}",
                restaurant_id=f"r{case}",
                name=f"Item {idx}",
                price_cents=rng.randint(100, 600),
                calories=rng.randint(50, 800),
                max_qty=rng.randint(0, 2),
            )
            for idx in range(item_count)
        ]
        deals = []
        if item_count:
            deals.append(
                Deal(
                    id="bogo",
                    type="buy_x_get_y",
                    description="BOGO",
                    item_id=menu[0].id,
                    buy_qty=1,
                    free_qty=1,
                )
            )
        if item_count > 1:
            deals.append(
                Deal(
                    id="fixed_over_6",
                    type="threshold_fixed_off",
                    description="$1 off over $6",
                    threshold_cents=600,
                    fixed_off_cents=100,
                )
            )
        restaurant = Restaurant(id=f"r{case}", name=f"R {case}", menu=menu, deals=deals)
        budget = 1200

        dp = optimize([restaurant], budget_cents=budget)
        brute = _brute_force_single_restaurant(restaurant, budget)

        assert (dp.total_calories, dp.total_cost_cents) == (
            brute.total_calories,
            brute.total_cost_cents,
        )


def _simple_restaurant(restaurant_id: str, price: int, calories: int) -> Restaurant:
    return Restaurant(
        id=restaurant_id,
        name=restaurant_id,
        menu=[MenuItem("item", restaurant_id, "Item", price, calories, 1)],
    )


def _bundle(restaurant_id: str, cost: int, calories: int) -> Bundle:
    return Bundle(
        restaurant_id=restaurant_id,
        restaurant_name=restaurant_id,
        items={"item": 1},
        item_names={"item": "Item"},
        pre_discount_subtotal_cents=cost,
        discounted_subtotal_cents=cost,
        final_cost_cents=cost,
        calories=calories,
    )


def _brute_force_single_restaurant(
    restaurant: Restaurant, budget_cents: int
):
    best = optimize([], budget_cents=budget_cents)
    ranges = [range(item.max_qty + 1) for item in restaurant.menu]
    for quantities in product(*ranges):
        items = {
            item.id: quantity
            for item, quantity in zip(restaurant.menu, quantities)
            if quantity
        }
        if not items:
            continue
        variants = _restaurant_from_quantities(restaurant, items)
        result = optimize([variants], budget_cents=budget_cents)
        if (
            result.total_calories,
            -result.total_cost_cents,
            -len(result.bundles),
        ) > (
            best.total_calories,
            -best.total_cost_cents,
            -len(best.bundles),
        ):
            best = result
    return best


def _restaurant_from_quantities(
    restaurant: Restaurant, quantities: dict[str, int]
) -> Restaurant:
    menu = []
    for item in restaurant.menu:
        max_qty = quantities.get(item.id, 0)
        menu.append(
            MenuItem(
                id=item.id,
                restaurant_id=item.restaurant_id,
                name=item.name,
                price_cents=item.price_cents,
                calories=item.calories,
                max_qty=max_qty,
                tags=item.tags,
            )
        )
    return Restaurant(
        id=restaurant.id,
        name=restaurant.name,
        menu=menu,
        deals=restaurant.deals,
        delivery_fee_cents=restaurant.delivery_fee_cents,
        service_fee_rate=restaurant.service_fee_rate,
        tax_rate=restaurant.tax_rate,
        tip_rate=restaurant.tip_rate,
        small_order_fee_cents=restaurant.small_order_fee_cents,
        small_order_threshold_cents=restaurant.small_order_threshold_cents,
    )

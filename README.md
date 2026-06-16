# DoorDash Optimizer

Python 3.10+ optimization engine for choosing restaurant baskets with the most calories under a budget.

This project takes restaurant menus, deals, and fees, then searches for the best possible basket under a final all-in price limit. It is built as a solver, not a UI. The focus is on correct results, clean data flow, and exact handling of costs and discounts.

## Objective

Maximize:

```text
(total calories, -final all-in cost, -restaurant count)
```

Subject to:

```text
final all-in cost <= budget
restaurants used <= max_restaurants
```

## Flow

1. Load restaurant menus from the FoodSpark API.
2. Build item options for each menu item.
3. Apply item deals and restaurant deals.
4. Build the pareto frontier for each restaurant.
5. Run sparse DP across restaurants.
6. Return the best basket under budget.

The solver works in stages so each part stays focused:

- Menu loading brings in restaurants, items, prices, calories, and deal data.
- Item expansion checks every valid quantity for each menu item.
- Deal evaluation handles BOGO, threshold discounts, free items, combo bundles, and coupon groups.
- Restaurant pruning keeps only strong basket choices before the global search.
- Global search combines restaurant baskets and respects the total budget and restaurant limit.
- Result formatting gives a readable explanation of the final basket.

## What It Uses

- menu items
- deals
- fees
- pareto frontier
- sparse DP

## FoodSpark API

Set these env vars:

```bash
export FOODSPARK_API_KEY="..."
export FOODSPARK_API_BASE_URL="https://your-foodspark-base-url"
export FOODSPARK_MENU_PATH_TEMPLATE="/restaurants/{restaurant_id}/menu"
export FOODSPARK_RESTAURANT_IDS="restaurant-id-1,restaurant-id-2"
```

Optional:

```bash
export FOODSPARK_AUTH_HEADER="Authorization"
export FOODSPARK_AUTH_PREFIX="Bearer"
export BUDGET_CENTS=3500
export MAX_RESTAURANTS=2
export FOODSPARK_ITEM_MAX_QTY=5
export DEFAULT_DELIVERY_FEE_CENTS=0
export DEFAULT_SERVICE_FEE_RATE=0
export DEFAULT_TAX_RATE=0
export DEFAULT_TIP_RATE=0
export DEFAULT_SMALL_ORDER_FEE_CENTS=0
export DEFAULT_SMALL_ORDER_THRESHOLD_CENTS=0
```

`FOODSPARK_MENU_PATH_TEMPLATE` is the menu path for one restaurant ID.
`FOODSPARK_RESTAURANT_IDS` is the list of restaurants to load.

FoodSpark is used as the data source for menus and item details. The solver does not depend on sample files or hardcoded restaurant logic. The API layer is kept separate so the optimization code stays independent from the data source.

## Core Pieces

`doordash_optimizer/models.py`

- data models for items, deals, restaurants, bundles, and results

`doordash_optimizer/deals.py`

- BOGO math
- threshold rules
- combo and coupon handling
- legal deal scenario selection

`doordash_optimizer/fees.py`

- final all-in cost calculation
- delivery, service, tax, tip, and small-order fee logic

`doordash_optimizer/solver.py`

- restaurant-level DP
- deal application
- pareto frontier pruning
- global optimization across restaurants

`doordash_optimizer/foodspark_api.py`

- FoodSpark config
- API client
- payload parsing
- conversion into solver input

## Run

```bash
python3 scripts/run_demo.py
```

## Test

```bash
python3 -m pytest
```

## Validation

The test suite covers:

- deal math
- fee math
- pareto pruning
- optimizer behavior
- brute force checks on tiny cases
- FoodSpark payload parsing
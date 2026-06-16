"""DoorDash Optimizer public API."""

from doordash_optimizer.explain import explain_result
from doordash_optimizer.foodspark_api import (
    FoodSparkClient,
    FoodSparkConfig,
    load_restaurants_from_foodspark_api,
    restaurant_from_foodspark_payload,
)
from doordash_optimizer.loader import load_restaurants
from doordash_optimizer.models import Bundle, Deal, MenuItem, OptimizationResult, Restaurant
from doordash_optimizer.solver import generate_restaurant_frontier, optimize

__all__ = [
    "Bundle",
    "Deal",
    "FoodSparkClient",
    "FoodSparkConfig",
    "MenuItem",
    "OptimizationResult",
    "Restaurant",
    "explain_result",
    "generate_restaurant_frontier",
    "load_restaurants",
    "load_restaurants_from_foodspark_api",
    "optimize",
    "restaurant_from_foodspark_payload",
]

import os

from doordash_optimizer.foodspark_api import (
    FoodSparkConfig,
    restaurant_from_foodspark_payload,
)


def test_foodspark_config_from_env() -> None:
    previous = dict(os.environ)
    os.environ["FOODSPARK_API_KEY"] = "key"
    os.environ["FOODSPARK_API_BASE_URL"] = "https://example.test"
    os.environ["FOODSPARK_MENU_PATH_TEMPLATE"] = "/menus/{restaurant_id}"
    os.environ["FOODSPARK_AUTH_HEADER"] = "x-api-key"
    os.environ["FOODSPARK_AUTH_PREFIX"] = ""

    try:
        config = FoodSparkConfig.from_env()
    finally:
        os.environ.clear()
        os.environ.update(previous)

    assert config.api_key == "key"
    assert config.base_url == "https://example.test"
    assert config.menu_path_template == "/menus/{restaurant_id}"
    assert config.auth_header == "x-api-key"
    assert config.auth_prefix == ""


def test_restaurant_from_foodspark_payload_parses_categorized_menu() -> None:
    restaurant = restaurant_from_foodspark_payload(
        {
            "restaurant": {"id": "store-1", "name": "API Restaurant"},
            "menu": {
                "categories": [
                    {
                        "name": "Entrees",
                        "items": [
                            {
                                "id": "item-1",
                                "name": "Bowl",
                                "available": True,
                                "price": "$12.99",
                                "nutrition": {"calories": 800},
                                "tags": ["spicy"],
                            },
                            {
                                "id": "inactive",
                                "name": "Inactive",
                                "available": False,
                                "price": 1,
                            },
                        ],
                    }
                ]
            },
            "offers": [
                {
                    "id": "deal-1",
                    "type": "threshold_fixed_off",
                    "description": "$5 off $25",
                    "threshold": "$25.00",
                    "discount_amount": "$5.00",
                }
            ],
        },
        delivery_fee_cents=199,
        service_fee_rate=0.1,
    )

    assert restaurant.id == "store-1"
    assert restaurant.name == "API Restaurant"
    assert len(restaurant.menu) == 1
    assert restaurant.menu[0].id == "item-1"
    assert restaurant.menu[0].price_cents == 1299
    assert restaurant.menu[0].calories == 800
    assert restaurant.menu[0].tags == ("Entrees", "spicy")
    assert restaurant.delivery_fee_cents == 199
    assert restaurant.service_fee_rate == 0.1
    assert restaurant.deals[0].id == "deal-1"
    assert restaurant.deals[0].threshold_cents == 2500
    assert restaurant.deals[0].fixed_off_cents == 500

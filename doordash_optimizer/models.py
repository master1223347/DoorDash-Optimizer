from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MenuItem:
    id: str
    restaurant_id: str
    name: str
    price_cents: int
    calories: int
    max_qty: int
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class Deal:
    id: str
    type: str
    description: str
    item_id: str | None = None
    buy_qty: int | None = None
    free_qty: int | None = None
    threshold_cents: int | None = None
    percent_off: float | None = None
    fixed_off_cents: int | None = None
    free_item_id: str | None = None
    combo_items: dict[str, int] | None = None
    combo_price_cents: int | None = None
    stack_group: str | None = None
    stackable: bool = True


@dataclass(frozen=True)
class Restaurant:
    id: str
    name: str
    menu: list[MenuItem]
    deals: list[Deal] = field(default_factory=list)
    delivery_fee_cents: int = 0
    service_fee_rate: float = 0.0
    tax_rate: float = 0.0
    tip_rate: float = 0.0
    small_order_fee_cents: int = 0
    small_order_threshold_cents: int = 0


@dataclass(frozen=True)
class Bundle:
    restaurant_id: str
    restaurant_name: str
    items: dict[str, int]
    item_names: dict[str, str]
    pre_discount_subtotal_cents: int
    discounted_subtotal_cents: int
    final_cost_cents: int
    calories: int
    deals_used: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class OptimizationResult:
    bundles: list[Bundle]
    total_cost_cents: int
    total_calories: int
    budget_cents: int

    @property
    def calories_per_dollar(self) -> float:
        if self.total_cost_cents == 0:
            return 0.0
        return self.total_calories / (self.total_cost_cents / 100)

from __future__ import annotations

from doordash_optimizer.models import Bundle, OptimizationResult


def explain_result(result: OptimizationResult) -> str:
    lines = [
        "DoorDash Optimizer result",
        f"Total cost: {_money(result.total_cost_cents)}",
        f"Budget: {_money(result.budget_cents)}",
        f"Total calories: {result.total_calories}",
        f"Calories per dollar: {result.calories_per_dollar:.1f}",
        f"Restaurants used: {len(result.bundles)}",
    ]

    for bundle in result.bundles:
        lines.extend(_explain_bundle(bundle))

    lines.append(
        "Why this wins: it maximizes calories within the all-in budget, then breaks ties "
        "by lower final cost and fewer restaurants."
    )
    return "\n".join(lines)


def _explain_bundle(bundle: Bundle) -> list[str]:
    lines = [
        "",
        f"{bundle.restaurant_name}",
        "Items:",
    ]
    for item_id, quantity in sorted(bundle.items.items()):
        lines.append(f"  - {quantity} x {bundle.item_names[item_id]}")
    lines.extend(
        [
            f"Pre-discount subtotal: {_money(bundle.pre_discount_subtotal_cents)}",
            f"Discounted subtotal: {_money(bundle.discounted_subtotal_cents)}",
            f"Final all-in cost: {_money(bundle.final_cost_cents)}",
            f"Calories: {bundle.calories}",
            f"Deals used: {', '.join(bundle.deals_used) if bundle.deals_used else 'none'}",
        ]
    )
    if _has_threshold_deal(bundle):
        lines.append(
            "Threshold note: the selected item mix reaches a deal threshold; any low-cost "
            "filler item in the basket is valuable because it unlocks the discount."
        )
    return lines


def _has_threshold_deal(bundle: Bundle) -> bool:
    return any("threshold" in deal_id or "over" in deal_id for deal_id in bundle.deals_used)


def _money(cents: int) -> str:
    return f"${cents / 100:.2f}"

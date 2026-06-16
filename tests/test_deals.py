from doordash_optimizer.deals import paid_units_for_buy_x_get_y


def test_bogo_paid_units() -> None:
    assert paid_units_for_buy_x_get_y(0, 1, 1) == 0
    assert paid_units_for_buy_x_get_y(1, 1, 1) == 1
    assert paid_units_for_buy_x_get_y(2, 1, 1) == 1
    assert paid_units_for_buy_x_get_y(3, 1, 1) == 2
    assert paid_units_for_buy_x_get_y(4, 1, 1) == 2


def test_buy_two_get_one_paid_units() -> None:
    assert paid_units_for_buy_x_get_y(1, 2, 1) == 1
    assert paid_units_for_buy_x_get_y(2, 2, 1) == 2
    assert paid_units_for_buy_x_get_y(3, 2, 1) == 2
    assert paid_units_for_buy_x_get_y(4, 2, 1) == 3

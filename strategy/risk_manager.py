def calculate_risk(balance, risk_percent=1):
    """
    Calculate maximum money to risk on one trade.
    """

    risk_amount = balance * (risk_percent / 100)

    return risk_amount


def calculate_stop_loss(entry_price, atr, signal, atr_multiplier=2):
    """
    Calculate stop-loss using ATR.
    """

    stop_distance = atr * atr_multiplier

    if signal == "BUY":
        stop_loss = entry_price - stop_distance

    elif signal == "SELL":
        stop_loss = entry_price + stop_distance

    else:
        stop_loss = None

    return stop_loss


def calculate_take_profit(
    entry_price,
    stop_loss,
    signal,
    reward_ratio=2
):
    """
    Calculate take-profit using risk/reward ratio.
    """

    if stop_loss is None:
        return None

    risk_distance = abs(entry_price - stop_loss)

    reward_distance = risk_distance * reward_ratio

    if signal == "BUY":
        take_profit = entry_price + reward_distance

    elif signal == "SELL":
        take_profit = entry_price - reward_distance

    else:
        take_profit = None

    return take_profit


def calculate_position_size(
    risk_amount,
    entry_price,
    stop_loss,
    tick_size,
    tick_value,
    volume_min,
    volume_max,
    volume_step
):
    """
    Calculate position size using the broker's
    tick size and tick value.

    This is a calculation only.
    It does NOT place an order.
    """

    if stop_loss is None:
        return 0

    if tick_size <= 0 or tick_value <= 0:
        raise ValueError("Invalid tick size or tick value.")

    if volume_step <= 0:
        raise ValueError("Invalid volume step.")

    # Price distance between entry and stop loss
    price_distance = abs(entry_price - stop_loss)

    # Number of ticks between entry and stop loss
    number_of_ticks = price_distance / tick_size

    # Money lost for 1 lot if SL is hit
    loss_per_lot = number_of_ticks * tick_value

    if loss_per_lot <= 0:
        return 0

    # Raw position size
    position_size = risk_amount / loss_per_lot

    # Round down to broker's volume step
    position_size = (
        int(position_size / volume_step) * volume_step
    )

    # Respect broker minimum
    if position_size < volume_min:
        return 0

    # Respect broker maximum
    if position_size > volume_max:
        position_size = volume_max

    return round(position_size, 2)
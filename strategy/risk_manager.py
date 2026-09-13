def calculate_risk(balance, risk_percent=1):
    """
    Calculate maximum money that can be risked.
    """

    return balance * (risk_percent / 100)


def calculate_stop_loss(
    entry_price,
    atr,
    signal,
    atr_multiplier=2
):
    """
    Calculate Stop Loss using ATR.

    BUY:
        SL = Entry - (ATR * multiplier)

    SELL:
        SL = Entry + (ATR * multiplier)
    """

    if signal == "BUY":

        return (
            entry_price -
            (atr * atr_multiplier)
        )

    elif signal == "SELL":

        return (
            entry_price +
            (atr * atr_multiplier)
        )

    return None


def calculate_take_profit(
    entry_price,
    stop_loss,
    signal,
    reward_ratio=2
):
    """
    Calculate Take Profit.

    Risk : Reward = 1 : reward_ratio
    """

    if stop_loss is None:
        return None

    risk_distance = abs(
        entry_price - stop_loss
    )

    reward_distance = (
        risk_distance *
        reward_ratio
    )

    if signal == "BUY":

        return (
            entry_price +
            reward_distance
        )

    elif signal == "SELL":

        return (
            entry_price -
            reward_distance
        )

    return None


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
    Calculate position size based on
    maximum monetary risk.
    """

    if stop_loss is None:
        return 0

    if tick_size <= 0:
        raise ValueError(
            "Invalid tick size."
        )

    if tick_value <= 0:
        raise ValueError(
            "Invalid tick value."
        )

    if volume_step <= 0:
        raise ValueError(
            "Invalid volume step."
        )

    price_distance = abs(
        entry_price - stop_loss
    )

    number_of_ticks = (
        price_distance / tick_size
    )

    loss_per_lot = (
        number_of_ticks *
        tick_value
    )

    if loss_per_lot <= 0:
        return 0

    position_size = (
        risk_amount /
        loss_per_lot
    )

    # Round DOWN to broker volume step
    position_size = (
        int(
            position_size /
            volume_step
        )
        * volume_step
    )

    if position_size < volume_min:
        return 0

    if position_size > volume_max:
        position_size = volume_max

    return round(
        position_size,
        2
    )
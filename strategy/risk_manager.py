def evaluate_risk(signal: str, close_price: float, risk_reward_ratio: float = 2.0, pips: float = 0.0020):
    """
    Provides risk levels (Stop Loss and Take Profit) based on signal type.
    """
    if signal == "BUY":
        stop_loss = close_price - pips
        take_profit = close_price + (pips * risk_reward_ratio)
    elif signal == "SELL":
        stop_loss = close_price + pips
        take_profit = close_price - (pips * risk_reward_ratio)
    else:
        stop_loss = None
        take_profit = None

    return {
        "stop_loss": round(stop_loss, 5) if stop_loss else None,
        "take_profit": round(take_profit, 5) if take_profit else None,
        "risk_reward_ratio": risk_reward_ratio
    }
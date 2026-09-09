def generate_signal(data):
    """
    Generate BUY / SELL / HOLD signal.

    Strategy:

    BUY:
        Price > EMA20
        EMA20 > EMA50
        RSI between 50 and 70

    SELL:
        Price < EMA20
        EMA20 < EMA50
        RSI between 30 and 50

    Otherwise:
        HOLD
    """

    if data.empty:
        return {
            "signal": "HOLD",
            "reason": "No market data available."
        }

    latest = data.iloc[-1]

    close = float(latest["Close"])
    ema20 = float(latest["EMA_20"])
    ema50 = float(latest["EMA_50"])
    rsi = float(latest["RSI_14"])

    # =====================================================
    # BUY
    # =====================================================

    if (
        close > ema20
        and ema20 > ema50
        and 50 <= rsi <= 70
    ):
        return {
            "signal": "BUY",
            "reason": (
                "Bullish trend: price is above EMA20, "
                "EMA20 is above EMA50, and RSI confirms "
                "bullish momentum."
            )
        }

    # =====================================================
    # SELL
    # =====================================================

    if (
        close < ema20
        and ema20 < ema50
        and 30 <= rsi <= 50
    ):
        return {
            "signal": "SELL",
            "reason": (
                "Bearish trend: price is below EMA20, "
                "EMA20 is below EMA50, and RSI confirms "
                "bearish momentum."
            )
        }

    # =====================================================
    # HOLD
    # =====================================================

    return {
        "signal": "HOLD",
        "reason": (
            "Market conditions do not satisfy "
            "the BUY or SELL strategy."
        )
    }
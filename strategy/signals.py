def generate_signal(data):
    """
    Generate BUY / SELL / HOLD signal.

    Strategy:
        EMA + RSI + MACD confirmation

    BUY conditions:
        1. Price > EMA20
        2. EMA20 > EMA50
        3. RSI between 50 and 70
        4. MACD > MACD Signal

    SELL conditions:
        1. Price < EMA20
        2. EMA20 < EMA50
        3. RSI between 30 and 50
        4. MACD < MACD Signal

    If all BUY conditions are satisfied:
        BUY

    If all SELL conditions are satisfied:
        SELL

    Otherwise:
        HOLD
    """

    # =====================================================
    # NO DATA
    # =====================================================

    if data.empty:
        return {
            "signal": "HOLD",
            "reason": "No market data available.",
            "conditions": [],
        }

    # =====================================================
    # LATEST MARKET DATA
    # =====================================================

    latest = data.iloc[-1]

    close = float(latest["Close"])
    ema20 = float(latest["EMA_20"])
    ema50 = float(latest["EMA_50"])
    rsi = float(latest["RSI_14"])
    macd = float(latest["MACD"])
    macd_signal = float(latest["MACD_Signal"])

    # =====================================================
    # BUY CONDITIONS
    # =====================================================

    buy_price = close > ema20
    buy_trend = ema20 > ema50
    buy_rsi = 50 <= rsi <= 70
    buy_macd = macd > macd_signal

    # =====================================================
    # SELL CONDITIONS
    # =====================================================

    sell_price = close < ema20
    sell_trend = ema20 < ema50
    sell_rsi = 30 <= rsi <= 50
    sell_macd = macd < macd_signal

    # =====================================================
    # BUY SIGNAL
    # =====================================================

    if (
        buy_price
        and buy_trend
        and buy_rsi
        and buy_macd
    ):
        conditions = [
            f"✓ Price {close:.2f} is above EMA20 {ema20:.2f}",
            f"✓ EMA20 {ema20:.2f} is above EMA50 {ema50:.2f}",
            f"✓ RSI {rsi:.2f} is within the BUY range 50–70",
            f"✓ MACD {macd:.5f} is above Signal {macd_signal:.5f}",
        ]

        return {
            "signal": "BUY",
            "reason": (
                "Bullish setup confirmed. "
                "All BUY conditions are satisfied."
            ),
            "conditions": conditions,
        }

    # =====================================================
    # SELL SIGNAL
    # =====================================================

    if (
        sell_price
        and sell_trend
        and sell_rsi
        and sell_macd
    ):
        conditions = [
            f"✓ Price {close:.2f} is below EMA20 {ema20:.2f}",
            f"✓ EMA20 {ema20:.2f} is below EMA50 {ema50:.2f}",
            f"✓ RSI {rsi:.2f} is within the SELL range 30–50",
            f"✓ MACD {macd:.5f} is below Signal {macd_signal:.5f}",
        ]

        return {
            "signal": "SELL",
            "reason": (
                "Bearish setup confirmed. "
                "All SELL conditions are satisfied."
            ),
            "conditions": conditions,
        }

    # =====================================================
    # HOLD
    # =====================================================

    conditions = []

    # -----------------------------------------------------
    # Price vs EMA20
    # -----------------------------------------------------

    if buy_price:
        conditions.append(
            f"✓ Price {close:.2f} is above EMA20 {ema20:.2f}"
        )
    else:
        conditions.append(
            f"✗ Price {close:.2f} is below EMA20 {ema20:.2f}"
        )

    # -----------------------------------------------------
    # EMA20 vs EMA50
    # -----------------------------------------------------

    if buy_trend:
        conditions.append(
            f"✓ EMA20 {ema20:.2f} is above EMA50 {ema50:.2f}"
        )
    else:
        conditions.append(
            f"✗ EMA20 {ema20:.2f} is below EMA50 {ema50:.2f}"
        )

    # -----------------------------------------------------
    # RSI
    # -----------------------------------------------------

    if buy_rsi:
        conditions.append(
            f"✓ RSI {rsi:.2f} is within the BUY range 50–70"
        )
    elif sell_rsi:
        conditions.append(
            f"✓ RSI {rsi:.2f} is within the SELL range 30–50"
        )
    elif rsi > 70:
        conditions.append(
            f"✗ RSI {rsi:.2f} is above 70 (overbought)"
        )
    elif rsi < 30:
        conditions.append(
            f"✗ RSI {rsi:.2f} is below 30 (oversold)"
        )
    else:
        conditions.append(
            f"✗ RSI {rsi:.2f} is outside the required range"
        )

    # -----------------------------------------------------
    # MACD
    # -----------------------------------------------------

    if buy_macd:
        conditions.append(
            f"✓ MACD {macd:.5f} is above Signal {macd_signal:.5f}"
        )
    else:
        conditions.append(
            f"✗ MACD {macd:.5f} is below Signal {macd_signal:.5f}"
        )

    # =====================================================
    # DETERMINE HOLD REASON
    # =====================================================

    if (
        buy_price
        and buy_trend
        and buy_macd
        and not buy_rsi
    ):
        reason = (
            "HOLD: Bullish conditions are present, "
            "but RSI does not confirm the BUY setup."
        )

    elif (
        sell_price
        and sell_trend
        and sell_macd
        and not sell_rsi
    ):
        reason = (
            "HOLD: Bearish conditions are present, "
            "but RSI does not confirm the SELL setup."
        )

    else:
        reason = (
            "HOLD: No complete BUY or SELL setup "
            "is currently confirmed."
        )

    return {
        "signal": "HOLD",
        "reason": reason,
        "conditions": conditions,
    }
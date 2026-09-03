def generate_signal(data):

    latest = data.iloc[-1]

    close = float(latest["Close"])
    ema20 = float(latest["EMA_20"])
    ema50 = float(latest["EMA_50"])
    rsi = float(latest["RSI_14"])

    # Bullish conditions
    bullish = (
        close > ema20
        and ema20 > ema50
        and 50 <= rsi <= 70
    )

    # Bearish conditions
    bearish = (
        close < ema20
        and ema20 < ema50
        and 30 <= rsi <= 50
    )

    if bullish:
        return "BUY"

    if bearish:
        return "SELL"

    return "HOLD"
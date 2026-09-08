import pandas as pd

from strategy.indicators import (
    calculate_ema,
    calculate_rsi,
    calculate_atr
)


def get_latest_signal(df: pd.DataFrame) -> dict:
    """
    Calculate technical indicators and generate
    a BUY / SELL / HOLD signal.
    """

    if df.empty:
        raise ValueError("Market data is empty.")

    required_columns = [
        "open",
        "high",
        "low",
        "close"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns: {missing_columns}"
        )

    df = df.copy()

    # ---------------------------------------------
    # Technical Indicators
    # ---------------------------------------------

    df["ema_20"] = calculate_ema(
        df,
        period=20
    )

    df["ema_50"] = calculate_ema(
        df,
        period=50
    )

    df["rsi_14"] = calculate_rsi(
        df,
        period=14
    )

    df["atr_14"] = calculate_atr(
        df,
        period=14
    )

    # Remove rows where indicators are not ready
    valid_data = df.dropna(
        subset=[
            "ema_20",
            "ema_50",
            "rsi_14",
            "atr_14"
        ]
    )

    if valid_data.empty:
        raise ValueError(
            "Not enough market data to calculate indicators."
        )

    latest = valid_data.iloc[-1]

    close_price = float(latest["close"])
    ema20 = float(latest["ema_20"])
    ema50 = float(latest["ema_50"])
    rsi = float(latest["rsi_14"])
    atr = float(latest["atr_14"])

    # ---------------------------------------------
    # Signal Logic
    # ---------------------------------------------

    bullish_trend = (
        close_price > ema20
        and ema20 > ema50
    )

    bearish_trend = (
        close_price < ema20
        and ema20 < ema50
    )

    bullish_momentum = (
        50 <= rsi <= 70
    )

    bearish_momentum = (
        30 <= rsi <= 50
    )

    if bullish_trend and bullish_momentum:

        signal = "BUY"

        reason = (
            "Price is above EMA20, "
            "EMA20 is above EMA50, "
            "and RSI confirms bullish momentum."
        )

    elif bearish_trend and bearish_momentum:

        signal = "SELL"

        reason = (
            "Price is below EMA20, "
            "EMA20 is below EMA50, "
            "and RSI confirms bearish momentum."
        )

    else:

        signal = "HOLD"

        if rsi > 70:
            reason = (
                "Trend may be bullish, "
                "but RSI is overbought."
            )

        elif rsi < 30:
            reason = (
                "Trend may be bearish, "
                "but RSI is oversold."
            )

        else:
            reason = (
                "EMA trend and RSI do not "
                "confirm a strong trading setup."
            )

    # ---------------------------------------------
    # Entry / Stop Loss / Take Profit
    # ---------------------------------------------

    entry = round(
        close_price,
        2
    )

    stop_loss = None
    take_profit = None

    # ATR-based risk management
    atr_multiplier = 2
    reward_ratio = 2

    if signal == "BUY":

        stop_loss = round(
            entry - (
                atr * atr_multiplier
            ),
            2
        )

        take_profit = round(
            entry + (
                atr * atr_multiplier * reward_ratio
            ),
            2
        )

    elif signal == "SELL":

        stop_loss = round(
            entry + (
                atr * atr_multiplier
            ),
            2
        )

        take_profit = round(
            entry - (
                atr * atr_multiplier * reward_ratio
            ),
            2
        )

    return {
        "price": round(close_price, 2),
        "ema_20": round(ema20, 2),
        "ema_50": round(ema50, 2),
        "rsi_14": round(rsi, 2),
        "atr_14": round(atr, 2),

        "signal": signal,

        "entry": entry,

        "stop_loss": stop_loss,

        "take_profit": take_profit,

        "reason": reason
    }
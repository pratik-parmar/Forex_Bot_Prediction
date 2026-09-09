from strategy.indicators import calculate_indicators
from strategy.signals import generate_signal
from strategy.risk_manager import (
    calculate_stop_loss,
    calculate_take_profit,
)


def calculate_technical_analysis(
    data,
    balance=150,
    risk_percent=1
):
    """
    Calculate indicators, trading signal,
    entry, stop loss and take profit.
    """

    # =====================================================
    # INDICATORS
    # =====================================================

    df = calculate_indicators(data)

    latest = df.iloc[-1]

    price = float(latest["Close"])
    ema20 = float(latest["EMA_20"])
    ema50 = float(latest["EMA_50"])
    rsi = float(latest["RSI_14"])
    atr = float(latest["ATR_14"])

    # =====================================================
    # SIGNAL
    # =====================================================

    signal_data = generate_signal(df)

    signal = signal_data["signal"]
    reason = signal_data["reason"]

    # =====================================================
    # ENTRY
    # =====================================================

    entry = None
    stop_loss = None
    take_profit = None

    if signal in ["BUY", "SELL"]:

        entry = price

        stop_loss = calculate_stop_loss(
            entry_price=entry,
            atr=atr,
            signal=signal,
            atr_multiplier=2
        )

        take_profit = calculate_take_profit(
            entry_price=entry,
            stop_loss=stop_loss,
            signal=signal,
            reward_ratio=2
        )

    return {
        "price": round(price, 5),

        "ema_20": round(ema20, 5),
        "ema_50": round(ema50, 5),

        "rsi_14": round(rsi, 2),
        "atr_14": round(atr, 5),

        "signal": signal,
        "reason": reason,

        "entry": (
            round(entry, 5)
            if entry is not None
            else None
        ),

        "stop_loss": (
            round(stop_loss, 5)
            if stop_loss is not None
            else None
        ),

        "take_profit": (
            round(take_profit, 5)
            if take_profit is not None
            else None
        ),

        "candles": len(df),
    }
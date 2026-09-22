import numpy as np
import pandas as pd
import pytest

from strategy.indicators import calculate_indicators
from strategy.signals import generate_signal
from strategy.risk_manager import (
    calculate_risk,
    calculate_stop_loss,
    calculate_take_profit,
    calculate_position_size,
)


def make_ohlc(rows=80):
    close = np.linspace(100, 120, rows) + np.sin(np.arange(rows) / 3)
    return pd.DataFrame(
        {
            "Open": close - 0.2,
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
        }
    )


def signal_row(close, ema20, ema50, rsi, macd, macd_signal):
    return pd.DataFrame([{
        "Close": close,
        "EMA_20": ema20,
        "EMA_50": ema50,
        "RSI_14": rsi,
        "MACD": macd,
        "MACD_Signal": macd_signal,
    }])


def test_indicators_add_expected_columns():
    result = calculate_indicators(make_ohlc())
    expected = {
        "EMA_20", "EMA_50", "RSI_14", "ATR_14",
        "MACD", "MACD_Signal", "MACD_Histogram",
        "BB_Upper", "BB_Middle", "BB_Lower",
    }
    assert expected.issubset(result.columns)
    assert len(result) > 0


def test_indicators_reject_missing_ohlc_column():
    with pytest.raises(ValueError, match="Missing required column"):
        calculate_indicators(pd.DataFrame({"Open": [1], "Close": [1]}))


def test_indicators_require_at_least_50_valid_candles():
    with pytest.raises(ValueError, match="At least 50 candles"):
        calculate_indicators(make_ohlc(30))


def test_generate_signal_returns_buy_for_confirmed_bullish_setup():
    result = generate_signal(signal_row(110, 108, 105, 60, 2.0, 1.0))
    assert result["signal"] == "BUY"
    assert "BUY conditions" in result["reason"]
    assert len(result["conditions"]) == 4


def test_generate_signal_returns_sell_for_confirmed_bearish_setup():
    result = generate_signal(signal_row(90, 95, 100, 40, -2.0, -1.0))
    assert result["signal"] == "SELL"
    assert "SELL conditions" in result["reason"]
    assert len(result["conditions"]) == 4


def test_generate_signal_returns_hold_for_mixed_setup():
    result = generate_signal(signal_row(110, 108, 105, 80, 2.0, 1.0))
    assert result["signal"] == "HOLD"
    assert result["reason"].startswith("HOLD:")


def test_generate_signal_handles_empty_dataframe():
    result = generate_signal(pd.DataFrame())
    assert result["signal"] == "HOLD"
    assert result["conditions"] == []


def test_risk_manager_calculations():
    assert calculate_risk(1000, 1) == 10
    assert calculate_stop_loss(100, 2, "BUY", 2) == 96
    assert calculate_stop_loss(100, 2, "SELL", 2) == 104
    assert calculate_take_profit(100, 96, "BUY", 2) == 108
    assert calculate_take_profit(100, 104, "SELL", 2) == 92


def test_position_size_returns_zero_without_stop_loss():
    assert calculate_position_size(
        risk_amount=10,
        entry_price=100,
        stop_loss=None,
        tick_size=0.01,
        tick_value=1,
        volume_min=0.01,
        volume_max=10,
        volume_step=0.01,
    ) == 0


def test_position_size_rejects_invalid_tick_size():
    with pytest.raises(ValueError, match="Invalid tick size"):
        calculate_position_size(
            risk_amount=10,
            entry_price=100,
            stop_loss=99,
            tick_size=0,
            tick_value=1,
            volume_min=0.01,
            volume_max=10,
            volume_step=0.01,
        )

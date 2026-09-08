import pandas as pd
import numpy as np


def calculate_sma(
    df: pd.DataFrame,
    period: int = 20,
    column: str = "close"
) -> pd.Series:
    """Calculate Simple Moving Average."""
    return df[column].rolling(window=period).mean()


def calculate_ema(
    df: pd.DataFrame,
    period: int = 20,
    column: str = "close"
) -> pd.Series:
    """Calculate Exponential Moving Average."""
    return df[column].ewm(
        span=period,
        adjust=False
    ).mean()


def calculate_rsi(
    df: pd.DataFrame,
    period: int = 14,
    column: str = "close"
) -> pd.Series:
    """
    Calculate RSI using Wilder's smoothing method.
    """

    delta = df[column].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    average_gain = gain.ewm(
        alpha=1 / period,
        min_periods=period,
        adjust=False
    ).mean()

    average_loss = loss.ewm(
        alpha=1 / period,
        min_periods=period,
        adjust=False
    ).mean()

    rs = average_gain / average_loss

    rsi = 100 - (
        100 / (1 + rs)
    )

    return rsi


def calculate_atr(
    df: pd.DataFrame,
    period: int = 14
) -> pd.Series:
    """
    Calculate Average True Range using
    the standard True Range calculation.
    """

    previous_close = df["close"].shift(1)

    true_range = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - previous_close).abs(),
            (df["low"] - previous_close).abs()
        ],
        axis=1
    ).max(axis=1)

    atr = true_range.ewm(
        alpha=1 / period,
        min_periods=period,
        adjust=False
    ).mean()

    return atr


def calculate_macd(
    df: pd.DataFrame,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
    column: str = "close",
) -> pd.DataFrame:

    fast_ema = df[column].ewm(
        span=fast_period,
        adjust=False
    ).mean()

    slow_ema = df[column].ewm(
        span=slow_period,
        adjust=False
    ).mean()

    macd = fast_ema - slow_ema

    signal_line = macd.ewm(
        span=signal_period,
        adjust=False
    ).mean()

    histogram = macd - signal_line

    return pd.DataFrame(
        {
            "macd": macd,
            "macd_signal": signal_line,
            "macd_hist": histogram
        },
        index=df.index
    )


def calculate_bollinger_bands(
    df: pd.DataFrame,
    period: int = 20,
    std_dev: int = 2,
    column: str = "close"
) -> pd.DataFrame:

    middle_band = calculate_sma(
        df,
        period=period,
        column=column
    )

    rolling_std = df[column].rolling(
        window=period
    ).std()

    upper_band = middle_band + (
        rolling_std * std_dev
    )

    lower_band = middle_band - (
        rolling_std * std_dev
    )

    return pd.DataFrame(
        {
            "bb_upper": upper_band,
            "bb_middle": middle_band,
            "bb_lower": lower_band
        },
        index=df.index
    )
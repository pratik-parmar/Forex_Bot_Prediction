import pandas as pd
import yfinance as yf


# =====================================================
# YAHOO FINANCE SYMBOLS
# =====================================================

YAHOO_SYMBOLS = {
    "XAUUSD": "GC=F",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "BTCUSD": "BTC-USD",
}


# =====================================================
# TIMEFRAME CONFIGURATION
# =====================================================

TIMEFRAME_CONFIG = {
    "1": {
        "interval": "1m",
        "period": "7d",
    },
    "5": {
        "interval": "5m",
        "period": "60d",
    },
    "15": {
        "interval": "15m",
        "period": "60d",
    },
    "30": {
        "interval": "30m",
        "period": "60d",
    },
    "60": {
        "interval": "60m",
        "period": "730d",
    },
    "D": {
        "interval": "1d",
        "period": "2y",
    },
}


def get_market_candles(
    symbol,
    timeframe="15"
):
    """
    Fetch historical OHLCV market candles.

    Supported symbols:
        XAUUSD
        EURUSD
        GBPUSD
        BTCUSD

    Supported timeframes:
        1
        5
        15
        30
        60
        D

    Data source:
        Yahoo Finance
    """

    # =====================================================
    # NORMALIZE SYMBOL
    # =====================================================

    symbol = symbol.upper()

    # =====================================================
    # VALIDATE SYMBOL
    # =====================================================

    if symbol not in YAHOO_SYMBOLS:
        raise ValueError(
            f"Unsupported market symbol: {symbol}"
        )

    # =====================================================
    # VALIDATE TIMEFRAME
    # =====================================================

    if timeframe not in TIMEFRAME_CONFIG:
        raise ValueError(
            f"Unsupported timeframe: {timeframe}"
        )

    yahoo_symbol = YAHOO_SYMBOLS[symbol]

    config = TIMEFRAME_CONFIG[timeframe]

    interval = config["interval"]
    period = config["period"]

    # =====================================================
    # FETCH DATA FROM YAHOO FINANCE
    # =====================================================

    try:
        df = yf.download(
            tickers=yahoo_symbol,
            period=period,
            interval=interval,
            progress=False,
            auto_adjust=False,
            threads=False,
        )

    except Exception as exc:
        raise ValueError(
            f"Yahoo Finance request failed for "
            f"{symbol}: {exc}"
        ) from exc

    # =====================================================
    # CHECK RESPONSE
    # =====================================================

    if df is None or df.empty:
        raise ValueError(
            f"No market candle data returned for "
            f"{symbol}."
        )

    # =====================================================
    # HANDLE YAHOO MULTI-INDEX COLUMNS
    # =====================================================

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # =====================================================
    # NORMALIZE COLUMN NAMES
    # =====================================================

    required_columns = [
        "Open",
        "High",
        "Low",
        "Close",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required market columns for "
            f"{symbol}: {missing_columns}"
        )

    # =====================================================
    # KEEP STANDARD OHLCV COLUMNS
    # =====================================================

    columns_to_keep = [
        "Open",
        "High",
        "Low",
        "Close",
    ]

    if "Volume" in df.columns:
        columns_to_keep.append("Volume")

    df = df[columns_to_keep].copy()

    # =====================================================
    # REMOVE INVALID ROWS
    # =====================================================

    df.dropna(
        subset=[
            "Open",
            "High",
            "Low",
            "Close",
        ],
        inplace=True
    )

    # =====================================================
    # ADD TIMESTAMP COLUMN
    # =====================================================

    df.reset_index(inplace=True)

    if "Datetime" in df.columns:
        df.rename(
            columns={
                "Datetime": "Timestamp"
            },
            inplace=True
        )

    elif "Date" in df.columns:
        df.rename(
            columns={
                "Date": "Timestamp"
            },
            inplace=True
        )

    # =====================================================
    # FINAL DATA CLEANUP
    # =====================================================

    if "Timestamp" not in df.columns:
        raise ValueError(
            f"Timestamp column is missing for {symbol}."
        )

    df.reset_index(drop=True, inplace=True)

    return df
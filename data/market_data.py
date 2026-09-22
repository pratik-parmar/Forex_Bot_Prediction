
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


# =====================================================
# NORMALIZE YAHOO FINANCE COLUMNS
# =====================================================

def normalize_market_columns(df):
    """
    Normalize Yahoo Finance column names.

    Handles MultiIndex columns returned by yfinance,
    such as ('Close', 'EURUSD=X').
    """

    if isinstance(df.columns, pd.MultiIndex):
        # Yahoo Finance commonly returns price fields
        # in the first level of the MultiIndex.
        df.columns = df.columns.get_level_values(0)

    # Normalize whitespace in column names.
    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    return df


# =====================================================
# NORMALIZE TIMESTAMP COLUMN
# =====================================================

def normalize_timestamp(df):
    """
    Ensure the DataFrame contains a Timestamp column.

    Handles:
        - Datetime column
        - Date column
        - timestamp / time columns
        - Unix timestamps
        - DatetimeIndex
        - Date index
        - Generic reset-index column
    """

    df = df.copy()

    # -------------------------------------------------
    # CASE 1: Timestamp already exists
    # -------------------------------------------------

    if "Timestamp" in df.columns:
        timestamp_col = "Timestamp"

    else:
        # -------------------------------------------------
        # CASE 2: Find a timestamp-like column
        # -------------------------------------------------

        timestamp_aliases = {
            "datetime",
            "date",
            "timestamp",
            "time",
            "index",
        }

        timestamp_col = None

        for column in df.columns:
            if str(column).strip().lower() in timestamp_aliases:
                timestamp_col = column
                break

        # -------------------------------------------------
        # CASE 3: Use the DataFrame index
        # -------------------------------------------------

        if timestamp_col is None:

            if isinstance(
                df.index,
                (pd.DatetimeIndex, pd.PeriodIndex)
            ):
                df["Timestamp"] = df.index
                timestamp_col = "Timestamp"

            else:
                # Try resetting the index in case it
                # contains the original date/time values.
                df = df.reset_index()

                for column in df.columns:
                    if str(column).strip().lower() in timestamp_aliases:
                        timestamp_col = column
                        break

    # -------------------------------------------------
    # CASE 4: No timestamp source found
    # -------------------------------------------------

    if timestamp_col is None:
        raise ValueError(
            "Timestamp column is missing."
        )

    # -------------------------------------------------
    # RENAME TIMESTAMP COLUMN
    # -------------------------------------------------

    if timestamp_col != "Timestamp":
        df.rename(
            columns={
                timestamp_col: "Timestamp"
            },
            inplace=True
        )

    # -------------------------------------------------
    # CONVERT UNIX TIMESTAMPS IF NECESSARY
    # -------------------------------------------------

    timestamp_values = df["Timestamp"]

    if pd.api.types.is_numeric_dtype(timestamp_values):

        valid_values = timestamp_values.dropna()

        if not valid_values.empty:
            median_value = valid_values.abs().median()

            # Infer common Unix timestamp units.
            if median_value >= 1e17:
                unit = "ns"
            elif median_value >= 1e14:
                unit = "us"
            elif median_value >= 1e11:
                unit = "ms"
            else:
                unit = "s"

            df["Timestamp"] = pd.to_datetime(
                timestamp_values,
                unit=unit,
                errors="coerce",
                utc=True
            )

    else:
        df["Timestamp"] = pd.to_datetime(
            timestamp_values,
            errors="coerce",
            utc=True
        )

    # -------------------------------------------------
    # REMOVE INVALID TIMESTAMP ROWS
    # -------------------------------------------------

    df.dropna(
        subset=["Timestamp"],
        inplace=True
    )

    return df


# =====================================================
# FETCH MARKET CANDLES
# =====================================================

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
    # NORMALIZE SYMBOL AND TIMEFRAME
    # =====================================================

    symbol = str(symbol).strip().upper()
    timeframe = str(timeframe).strip().upper()

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

    df = df.copy()

    # =====================================================
    # NORMALIZE COLUMNS
    # =====================================================

    df = normalize_market_columns(df)

    # =====================================================
    # VALIDATE REQUIRED OHLC COLUMNS
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
    # REMOVE INVALID OHLC ROWS
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
    # NORMALIZE TIMESTAMP
    # =====================================================

    df = normalize_timestamp(df)

    # =====================================================
    # FINAL DATA CLEANUP
    # =====================================================

    # Keep timestamps in ascending order.
    df.sort_values(
        by="Timestamp",
        inplace=True
    )

    df.reset_index(
        drop=True,
        inplace=True
    )

    return df
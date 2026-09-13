import pandas as pd


def calculate_indicators(data):
    """
    Calculate technical indicators for any supported symbol.

    Required columns:
        Open, High, Low, Close

    Current indicators:
        EMA 20
        EMA 50
        RSI 14
        ATR 14
        MACD (12, 26, 9)
    """

    df = data.copy()

    # Normalize column names
    df.columns = [
        str(col).strip().title()
        for col in df.columns
    ]

    required_columns = [
        "Open",
        "High",
        "Low",
        "Close"
    ]

    for column in required_columns:
        if column not in df.columns:
            raise ValueError(
                f"Missing required column: {column}"
            )

    # Make sure prices are numeric
    for column in required_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    df = df.dropna(
        subset=required_columns
    )

    if len(df) < 50:
        raise ValueError(
            f"Not enough candles. "
            f"At least 50 candles are required, "
            f"received {len(df)}."
        )

    # =====================================================
    # EMA 20
    # =====================================================

    df["EMA_20"] = (
        df["Close"]
        .ewm(
            span=20,
            adjust=False
        )
        .mean()
    )

    # =====================================================
    # EMA 50
    # =====================================================

    df["EMA_50"] = (
        df["Close"]
        .ewm(
            span=50,
            adjust=False
        )
        .mean()
    )

    # =====================================================
    # RSI 14
    # =====================================================

    delta = df["Close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    average_gain = (
        gain
        .rolling(window=14)
        .mean()
    )

    average_loss = (
        loss
        .rolling(window=14)
        .mean()
    )

    rs = average_gain / average_loss

    df["RSI_14"] = (
        100 -
        (
            100 /
            (1 + rs)
        )
    )

    # =====================================================
    # ATR 14
    # =====================================================

    previous_close = df["Close"].shift(1)

    true_range = pd.concat(
        [
            df["High"] - df["Low"],

            (
                df["High"] -
                previous_close
            ).abs(),

            (
                df["Low"] -
                previous_close
            ).abs()
        ],
        axis=1
    ).max(axis=1)

    df["ATR_14"] = (
        true_range
        .rolling(window=14)
        .mean()
    )

    # =====================================================
    # MACD (12, 26, 9)
    # =====================================================

    ema12 = (
        df["Close"]
        .ewm(
            span=12,
            adjust=False
        )
        .mean()
    )

    ema26 = (
        df["Close"]
        .ewm(
            span=26,
            adjust=False
        )
        .mean()
    )

    df["MACD"] = ema12 - ema26

    df["MACD_Signal"] = (
        df["MACD"]
        .ewm(
            span=9,
            adjust=False
        )
        .mean()
    )

    df["MACD_Histogram"] = (
        df["MACD"] -
        df["MACD_Signal"]
    )

    return df

import pandas as pd


def calculate_indicators(data):

    df = data.copy()

    # Handle Yahoo Finance multi-level columns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Make sure required columns exist
    required_columns = ["Open", "High", "Low", "Close"]

    for column in required_columns:
        if column not in df.columns:
            raise ValueError(f"Missing column: {column}")

    # EMA
    df["EMA_20"] = df["Close"].ewm(
        span=20,
        adjust=False
    ).mean()

    df["EMA_50"] = df["Close"].ewm(
        span=50,
        adjust=False
    ).mean()

    # RSI
    delta = df["Close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    average_gain = gain.rolling(14).mean()
    average_loss = loss.rolling(14).mean()

    rs = average_gain / average_loss

    df["RSI_14"] = 100 - (100 / (1 + rs))

    # ATR
    previous_close = df["Close"].shift(1)

    true_range = pd.concat(
        [
            df["High"] - df["Low"],
            (df["High"] - previous_close).abs(),
            (df["Low"] - previous_close).abs()
        ],
        axis=1
    ).max(axis=1)

    df["ATR_14"] = true_range.rolling(14).mean()

    return df
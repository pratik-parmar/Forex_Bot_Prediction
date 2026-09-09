import os
import requests
import pandas as pd


FINNHUB_REST_URL = (
    "https://finnhub.io/api/v1/forex/candle"
)

FINNHUB_SYMBOLS = {
    "XAUUSD": "OANDA:XAU_USD",
    "EURUSD": "OANDA:EUR_USD",
    "GBPUSD": "OANDA:GBP_USD",
}

TIMEFRAME_SECONDS = {
    "1": 60,
    "5": 300,
    "15": 900,
    "30": 1800,
    "60": 3600,
    "D": 86400,
}


def get_market_candles(
    symbol,
    timeframe="15"
):

    symbol = symbol.upper()

    api_key = os.getenv(
        "FINNHUB_API_KEY",
        ""
    ).strip()

    if not api_key:
        raise ValueError(
            "FINNHUB_API_KEY is not configured."
        )

    if timeframe not in TIMEFRAME_SECONDS:
        raise ValueError(
            f"Unsupported timeframe: {timeframe}"
        )

    # =====================================================
    # FINNHUB SYMBOL
    # =====================================================

    if symbol in FINNHUB_SYMBOLS:

        resolution = (
            "D"
            if timeframe == "D"
            else timeframe
        )

        import time

        end_time = int(time.time())

        # Get enough candles for EMA50
        start_time = (
            end_time -
            (
                TIMEFRAME_SECONDS[timeframe]
                * 200
            )
        )

        response = requests.get(
            FINNHUB_REST_URL,
            params={
                "symbol": FINNHUB_SYMBOLS[symbol],
                "resolution": resolution,
                "from": start_time,
                "to": end_time,
                "token": api_key,
            },
            timeout=15
        )

        response.raise_for_status()

        payload = response.json()

        if payload.get("s") != "ok":
            raise ValueError(
                f"Finnhub candle error: {payload}"
            )

        df = pd.DataFrame(
            {
                "Open": payload["o"],
                "High": payload["h"],
                "Low": payload["l"],
                "Close": payload["c"],
                "Volume": payload.get(
                    "v",
                    []
                ),
                "Timestamp": payload["t"],
            }
        )

        return df

    # =====================================================
    # BTCUSD
    # =====================================================

    if symbol == "BTCUSD":

        url = (
            "https://finnhub.io/api/v1/crypto/candle"
        )

        resolution = (
            "D"
            if timeframe == "D"
            else timeframe
        )

        import time

        end_time = int(time.time())

        start_time = (
            end_time -
            (
                TIMEFRAME_SECONDS[timeframe]
                * 200
            )
        )

        response = requests.get(
            url,
            params={
                "symbol": "BINANCE:BTCUSDT",
                "resolution": resolution,
                "from": start_time,
                "to": end_time,
                "token": api_key,
            },
            timeout=15
        )

        response.raise_for_status()

        payload = response.json()

        if payload.get("s") != "ok":
            raise ValueError(
                f"Finnhub BTC candle error: {payload}"
            )

        df = pd.DataFrame(
            {
                "Open": payload["o"],
                "High": payload["h"],
                "Low": payload["l"],
                "Close": payload["c"],
                "Volume": payload.get(
                    "v",
                    []
                ),
                "Timestamp": payload["t"],
            }
        )

        return df

    raise ValueError(
        f"Unsupported market symbol: {symbol}"
    )
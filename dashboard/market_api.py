import pandas as pd
import yfinance as yf

from django.http import JsonResponse


# =========================================================
# SYMBOL MAPPING
# =========================================================

SYMBOL_MAP = {
    "XAUUSD": "GC=F",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "BTCUSD": "BTC-USD",
}


# =========================================================
# TIMEFRAME MAPPING
# =========================================================

TIMEFRAME_MAP = {
    "1": {
        "interval": "1m",
        "period": "7d",
        "label": "1m",
    },

    "5": {
        "interval": "5m",
        "period": "60d",
        "label": "5m",
    },

    "15": {
        "interval": "15m",
        "period": "60d",
        "label": "15m",
    },

    "30": {
        "interval": "30m",
        "period": "60d",
        "label": "30m",
    },

    "60": {
        "interval": "60m",
        "period": "1y",
        "label": "1H",
    },

    "D": {
        "interval": "1d",
        "period": "5y",
        "label": "1D",
    },
}


# =========================================================
# CLEAN YAHOO DATA
# =========================================================

def clean_dataframe(data):

    if data is None or data.empty:
        return pd.DataFrame()

    if isinstance(data.columns, pd.MultiIndex):

        data.columns = [
            str(column[0]).lower()
            for column in data.columns
        ]

    else:

        data.columns = [
            str(column).lower()
            for column in data.columns
        ]

    required_columns = [
        "open",
        "high",
        "low",
        "close",
    ]

    for column in required_columns:

        if column not in data.columns:

            raise ValueError(
                f"Missing market column: {column}"
            )

    data = data[
        ~data.index.duplicated(
            keep="last"
        )
    ]

    data = data.sort_index()

    return data


# =========================================================
# FETCH MARKET DATA
# =========================================================

def fetch_market_data(
    display_symbol="XAUUSD",
    timeframe="15"
):

    yahoo_symbol = SYMBOL_MAP.get(
        display_symbol
    )

    timeframe_config = TIMEFRAME_MAP.get(
        timeframe
    )

    if yahoo_symbol is None:

        raise ValueError(
            f"Unsupported symbol: {display_symbol}"
        )

    if timeframe_config is None:

        raise ValueError(
            f"Unsupported timeframe: {timeframe}"
        )

    data = yf.download(
        tickers=yahoo_symbol,
        period=timeframe_config["period"],
        interval=timeframe_config["interval"],
        auto_adjust=False,
        progress=False,
        threads=False,
    )

    return clean_dataframe(data)


# =========================================================
# LIVE PRICE API
# =========================================================

def live_price(request):

    symbol = request.GET.get(
        "symbol",
        "XAUUSD"
    ).upper()

    try:

        yahoo_symbol = SYMBOL_MAP.get(
            symbol
        )

        if yahoo_symbol is None:

            return JsonResponse(
                {
                    "success": False,
                    "error":
                        f"Unsupported symbol: {symbol}"
                },
                status=400,
            )

        # -------------------------------------------------
        # Fetch latest 1-minute market data
        # -------------------------------------------------

        data = yf.download(
            tickers=yahoo_symbol,
            period="1d",
            interval="1m",
            auto_adjust=False,
            progress=False,
            threads=False,
        )

        data = clean_dataframe(data)

        if data.empty:

            return JsonResponse(
                {
                    "success": False,
                    "error":
                        "No live market data available."
                },
                status=503,
            )

        # -------------------------------------------------
        # Latest candle
        # -------------------------------------------------

        latest = data.iloc[-1]

        price = float(
            latest["close"]
        )

        timestamp = data.index[-1]

        return JsonResponse(
            {
                "success": True,

                "symbol": symbol,

                "source_symbol":
                    yahoo_symbol,

                "price":
                    round(price, 2),

                "timestamp":
                    timestamp.isoformat(),

                "source":
                    "Yahoo Finance",
            }
        )

    except Exception as error:

        print(
            "Live price error:",
            error
        )

        return JsonResponse(
            {
                "success": False,
                "error": str(error),
            },
            status=500,
        )


# =========================================================
# MARKET CANDLES API
# =========================================================

def market_candles(request):

    symbol = request.GET.get(
        "symbol",
        "XAUUSD"
    ).upper()

    timeframe = request.GET.get(
        "timeframe",
        "15"
    )

    try:

        data = fetch_market_data(
            symbol,
            timeframe
        )

        if data.empty:

            return JsonResponse(
                {
                    "success": False,
                    "error":
                        "No market data available."
                },
                status=503,
            )

        candles = []

        for index, row in data.iterrows():

            candles.append(
                {
                    "time":
                        int(index.timestamp()),

                    "open":
                        float(row["open"]),

                    "high":
                        float(row["high"]),

                    "low":
                        float(row["low"]),

                    "close":
                        float(row["close"]),
                }
            )

        return JsonResponse(
            {
                "success": True,

                "symbol": symbol,

                "timeframe": timeframe,

                "candles": candles,
            }
        )

    except Exception as error:

        print(
            "Market candles error:",
            error
        )

        return JsonResponse(
            {
                "success": False,
                "error": str(error),
            },
            status=500,
        )
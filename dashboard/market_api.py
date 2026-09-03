from django.http import JsonResponse

from data.market_data import get_forex_data


def market_candles(request):

    timeframe = request.GET.get("timeframe", "15m")

    allowed_timeframes = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "4h": "1h",
        "1d": "1d",
    }

    interval = allowed_timeframes.get(timeframe)

    if interval is None:
        return JsonResponse(
            {
                "error": "Invalid timeframe",
                "allowed": list(allowed_timeframes.keys())
            },
            status=400
        )

    # Yahoo Finance has restrictions on intraday history.
    if timeframe == "1m":
        period = "5d"

    elif timeframe in ["5m", "15m", "30m"]:
        period = "5d"

    elif timeframe == "1h":
        period = "1mo"

    elif timeframe == "4h":
        period = "3mo"

    else:
        period = "1y"

    data = get_forex_data(
        symbol="GC=F",
        period=period,
        interval=interval
    )

    # Flatten Yahoo Finance MultiIndex columns
    if hasattr(data.columns, "levels"):
        data.columns = data.columns.get_level_values(0)

    candles = []

    for index, row in data.iterrows():

        candles.append({
            "time": int(index.timestamp()),
            "open": float(row["Open"]),
            "high": float(row["High"]),
            "low": float(row["Low"]),
            "close": float(row["Close"]),
        })

    return JsonResponse({
        "symbol": "XAUUSD",
        "timeframe": timeframe,
        "candles": candles
    })
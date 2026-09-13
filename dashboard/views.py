from django.http import JsonResponse
from django.shortcuts import render

from dashboard.technical import calculate_technical_analysis
from data.market_data import get_market_candles


SUPPORTED_SYMBOLS = {
    "XAUUSD",
    "EURUSD",
    "GBPUSD",
    "BTCUSD",
}


def dashboard_index(request):
    return render(
        request,
        "dashboard/index.html"
    )


def technical_analysis(request):

    symbol = request.GET.get(
        "symbol",
        "XAUUSD"
    ).upper()

    timeframe = request.GET.get(
        "timeframe",
        "15"
    )

    # =====================================================
    # VALIDATE SYMBOL
    # =====================================================

    if symbol not in SUPPORTED_SYMBOLS:

        return JsonResponse(
            {
                "success": False,
                "error": (
                    f"Unsupported symbol: {symbol}"
                )
            },
            status=400
        )

    try:

        # =================================================
        # GET CANDLES
        # =================================================

        candles = get_market_candles(
            symbol=symbol,
            timeframe=timeframe
        )

        # =================================================
        # TECHNICAL ANALYSIS
        # =================================================

        analysis = calculate_technical_analysis(
            candles,
            balance=150,
            risk_percent=1
        )

        analysis["success"] = True
        analysis["symbol"] = symbol
        analysis["timeframe"] = timeframe

        analysis["timeframe_label"] = (
            {
                "1": "1m",
                "5": "5m",
                "15": "15m",
                "30": "30m",
                "60": "1H",
                "D": "1D",
            }
            .get(
                timeframe,
                timeframe
            )
        )

        return JsonResponse(
            analysis
        )

    except Exception as error:

        return JsonResponse(
            {
                "success": False,
                "symbol": symbol,
                "error": str(error)
            },
            status=500
        )
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse
from django.shortcuts import redirect, render

from dashboard.technical import calculate_technical_analysis
from data.market_data import get_market_candles
from dashboard.decorators import api_login_required


SUPPORTED_SYMBOLS = {
    "XAUUSD",
    "EURUSD",
    "GBPUSD",
    "BTCUSD",
}


# =========================================================
# DASHBOARD
# =========================================================

@login_required
def dashboard_index(request):
    return render(
        request,
        "dashboard/index.html"
    )


# =========================================================
# LOGIN
# =========================================================

def login_view(request):

    if request.user.is_authenticated:
        return redirect("dashboard_index")

    if request.method == "POST":

        form = AuthenticationForm(
            request,
            data=request.POST
        )

        if form.is_valid():

            user = form.get_user()

            login(
                request,
                user
            )

            return redirect(
                request.GET.get(
                    "next",
                    "dashboard_index"
                )
            )

    else:

        form = AuthenticationForm()

    return render(
        request,
        "dashboard/login.html",
        {
            "form": form
        }
    )


# =========================================================
# REGISTER
# =========================================================

def register_view(request):

    if request.user.is_authenticated:
        return redirect("dashboard_index")

    from dashboard.forms import RegisterForm

    if request.method == "POST":

        form = RegisterForm(
            request.POST
        )

        if form.is_valid():

            user = form.save()

            login(
                request,
                user
            )

            messages.success(
                request,
                "Account created successfully."
            )

            return redirect(
                "dashboard_index"
            )

    else:

        form = RegisterForm()

    return render(
        request,
        "dashboard/register.html",
        {
            "form": form
        }
    )


# =========================================================
# LOGOUT
# =========================================================

@login_required
def logout_view(request):

    logout(request)

    return redirect(
        "login"
    )


# =========================================================
# TECHNICAL ANALYSIS API
# =========================================================

@api_login_required
def technical_analysis(request):

    symbol = request.GET.get(
        "symbol",
        "XAUUSD"
    ).upper()

    timeframe = request.GET.get(
        "timeframe",
        "15"
    )

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

        candles = get_market_candles(
            symbol=symbol,
            timeframe=timeframe
        )

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
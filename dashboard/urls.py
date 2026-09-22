from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

from .views import password_reset_request

from django.urls import path

from . import views

from .market_api import (
    live_price,
    market_candles,
    markets_overview,
)


urlpatterns = [

    # =================================================
    # AUTHENTICATION
    # =================================================

    path(
        "login/",
        views.login_view,
        name="login"
    ),

    path(
        "register/",
        views.register_view,
        name="register"
    ),

    path(
        "verify-email/<str:uidb64>/",
        views.verify_email_view,
        name="verify_email"
    ),

    path(
        "logout/",
        views.logout_view,
        name="logout"
    ),


    # =================================================
    # DASHBOARD
    # =================================================

    path(
        "",
        views.dashboard_index,
        name="dashboard_index"
    ),


    # =================================================
    # TECHNICAL ANALYSIS
    # =================================================

    path(
        "api/technical-analysis/",
        views.technical_analysis,
        name="technical_analysis"
    ),


    # =================================================
    # LIVE PRICE
    # =================================================

    path(
        "api/live-price/",
        live_price,
        name="live_price"
    ),


    # =================================================
    # MARKETS OVERVIEW
    # =================================================

    path(
        "api/markets/",
        markets_overview,
        name="markets_overview"
    ),


    # =================================================
    # MARKET CANDLES
    # =================================================

    path(
        "api/market-candles/",
        market_candles,
        name="market_candles"
    ),

    # Password reset
        # =================================================
# PASSWORD RESET
# =================================================

path(
    "password-reset/",
    password_reset_request,
    name="password_reset",
),

path(
    "password-reset/done/",
    auth_views.PasswordResetDoneView.as_view(
        template_name="dashboard/auth/password_reset_done.html"
    ),
    name="password_reset_done",
),

path(
    "password-reset/confirm/<uidb64>/<token>/",
    auth_views.PasswordResetConfirmView.as_view(
        template_name="dashboard/auth/password_reset_confirm.html",
        success_url=reverse_lazy("password_reset_complete"),
    ),
    name="password_reset_confirm",
),

path(
    "password-reset/complete/",
    auth_views.PasswordResetCompleteView.as_view(
        template_name="dashboard/auth/password_reset_complete.html"
    ),
    name="password_reset_complete",
),

]
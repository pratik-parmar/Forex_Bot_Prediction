from django.urls import path

from . import views

from .market_api import (
    live_price,
    market_candles,
)


urlpatterns = [

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
    # MARKET CANDLES
    # =================================================

    path(
        "api/market-candles/",
        market_candles,
        name="market_candles"
    ),

]
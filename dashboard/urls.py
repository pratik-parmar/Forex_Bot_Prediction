from django.urls import path

from . import views

from .market_api import (
    live_price,
    market_candles,
    markets_overview,
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

]
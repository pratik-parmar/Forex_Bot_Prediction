from django.urls import path

from . import views
from .market_api import (
    live_price,
    market_candles,
)


urlpatterns = [

    # Dashboard
    path(
        "",
        views.dashboard_index,
        name="dashboard_index"
    ),

    # Live price
    path(
        "api/live-price/",
        live_price,
        name="live_price"
    ),

    # Candles
    path(
        "api/market-candles/",
        market_candles,
        name="market_candles"
    ),
]
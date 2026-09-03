from django.urls import path

from .views import dashboard
from .market_api import market_candles


urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("api/market-candles/", market_candles, name="market_candles"),
]
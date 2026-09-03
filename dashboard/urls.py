from django.urls import path
from . import views
from .market_api import market_candles

urlpatterns = [
    path('', views.index, name='index'),
    path('api/market-candles/', market_candles, name='market_candles'),
]
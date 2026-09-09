from django.urls import path

from .consumers import MarketConsumer


websocket_urlpatterns = [

    path(
        "ws/dashboard/realtime/",
        MarketConsumer.as_asgi()
    ),

]
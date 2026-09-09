import os

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "forex_web.settings"
)

from django.core.asgi import get_asgi_application

from channels.routing import (
    ProtocolTypeRouter,
    URLRouter
)

from channels.auth import (
    AuthMiddlewareStack
)

from dashboard.routing import (
    websocket_urlpatterns
)

from dashboard.realtime import (
    live_market_feed
)


django_asgi_app = (
    get_asgi_application()
)


# Start Finnhub feed once
live_market_feed.start()


application = ProtocolTypeRouter({

    "http":
        django_asgi_app,

    "websocket":
        AuthMiddlewareStack(

            URLRouter(
                websocket_urlpatterns
            )

        ),
})
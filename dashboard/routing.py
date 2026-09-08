from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/dashboard/realtime/$', consumers.ForexLiveConsumer.as_asgi()),
]
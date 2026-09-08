from django.apps import AppConfig


class DashboardConfig(AppConfig):

    default_auto_field = "django.db.models.BigAutoField"

    name = "dashboard"

    def ready(self):

        import os

        if os.environ.get("RUN_MAIN") != "true":
            return

        from dashboard.realtime import live_market_feed

        live_market_feed.start()
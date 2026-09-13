from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path("admin/", admin.site.urls),

    # Forex Dashboard
    path("", include("dashboard.urls")),

    # Mutual Fund Dashboard
    path("mutual-funds/", include("mutual_funds.urls")),
]
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_index, name='dashboard_index'),
    path('api/prediction/', views.api_prediction, name='api_prediction'),
]
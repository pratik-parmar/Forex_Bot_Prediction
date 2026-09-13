from django.urls import path
from . import views

app_name = 'mutual_funds'

urlpatterns = [
    path('', views.fund_list, name='fund_list'),
    path('fund/<str:scheme_code>/', views.fund_detail, name='fund_detail'),
    path('api/fund/<str:scheme_code>/', views.fund_chart_api, name='fund_chart_api'),
]
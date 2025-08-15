from django.urls import path
from . import views

urlpatterns = [
    path('', views.login, name='login'),
    path('api/ping/', views.ping, name='ping'),          # simple JSON endpoint
]
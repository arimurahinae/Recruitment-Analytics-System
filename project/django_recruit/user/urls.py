from django.urls import path

from . import views

urlpatterns = [
    path("auth/register/", views.api_register, name="api_register"),
    path("auth/login/", views.api_login, name="api_login"),
    path("auth/logout/", views.api_logout, name="api_logout"),
    path("auth/me/", views.api_me, name="api_me"),
]

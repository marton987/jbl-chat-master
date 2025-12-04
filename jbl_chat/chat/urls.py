from django.urls import path
from . import views

app_name = "chat"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.CustomLogoutView.as_view(), name="logout"),
]

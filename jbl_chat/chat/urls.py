from django.urls import path

from . import views

app_name = "chat"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    # Keep users/ as an alias for flexibility
    path("users/", views.HomeView.as_view(), name="user_list"),
    path("chat/<str:username>/", views.ConversationView.as_view(), name="conversation"),
]

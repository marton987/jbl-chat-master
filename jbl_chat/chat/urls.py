from django.urls import path

from . import views

app_name = "chat"

urlpatterns = [
    path("", views.home, name="home"),
    path("users/", views.user_list, name="user_list"),
    path("chats/", views.conversations, name="conversations"),
    path("chat/<str:username>/", views.ConversationView.as_view(), name="conversation"),
    path(
        "chat/<str:username>/send/",
        views.ConversationView.as_view(),
        name="send_message",
    ),
    path(
        "chat/<str:username>/archive/",
        views.archive_conversation,
        name="archive_conversation",
    ),
    path(
        "chat/<str:username>/unarchive/",
        views.unarchive_conversation,
        name="unarchive_conversation",
    ),
]

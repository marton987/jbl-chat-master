from django.urls import path

from . import views

app_name = "chat"

urlpatterns = [
    path("", views.home, name="home"),
    path("users/", views.user_list, name="user_list"),
    path("chats/", views.conversations, name="conversations"),
    path("<str:username>/", views.conversation, name="conversation"),
    path(
        "chat/<str:username>/load-more/",
        views.load_more_messages,
        name="load_more_messages",
    ),
    path(
        "chat/<str:username>/send/",
        views.send_message,
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
    path(
        "chat/<str:username>/stream/",
        views.stream_messages,
        name="stream_messages",
    ),
]

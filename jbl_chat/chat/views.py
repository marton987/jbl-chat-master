from django.shortcuts import render
from django.http import HttpResponse
import datetime


def home(request):
    """Home page with HTMX test interactions"""
    return render(request, "chat/home.html")

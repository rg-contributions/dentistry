"""Dentistry URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from DentistryApp import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.main, name="view-main"),
    path("home", views.home),
    path("register", views.register),
    path("do_register", views.do_register),
    path("check_login", views.check_login),
    path("do_reserve", views.do_reserve),
    path("do_login", views.do_login),
    path("do_logout", views.do_logout),
    path("past_reservations", views.past_reservations),
    path("check_date", views.check_date),
]

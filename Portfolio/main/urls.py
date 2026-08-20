from django.contrib import admin
from django.urls import path
from . import views

from .views import email_contact

urlpatterns = [
    path('', views.index, name='index'),
    path('email/', email_contact, name='email'),
]
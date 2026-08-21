from django.contrib import admin
from django.urls import path
from . import views
from . import  test


urlpatterns = [
    path('', views.index, name='index'),
    path('email/', views.email_contact, name='email'),
    path('test', test.test, name='test'),
]
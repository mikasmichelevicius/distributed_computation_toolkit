
from django.urls import path, include
from django.contrib import admin
from . import views

app_name = 'computation'
urlpatterns = [
        path('', views.index, name = 'index'),
        path('home/', views.home, name = 'home'),
        path('login_user/', views.login_user, name = 'login_user'),
        path('sign_up/', views.sign_up, name = 'sign_up'),
        ]

from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.contrib import admin
from . import views

app_name = 'computation'
urlpatterns = [
        path('', views.index, name = 'index'),
        path('home/', views.home, name = 'home'),
        path('clients/', views.clients, name='clients'),
        path('params/', views.params, name='params'),
        path('queue/', views.queue, name='queue'),
        path('submit/', views.submit, name='submit'),
        path('completed/', views.completed, name='completed'),
        path('details/<str:job>/', views.details, name='details'),
        path('login_user/', views.login_user, name = 'login_user'),
        path('sign_up/', views.sign_up, name = 'sign_up'),
        path('logout_user/', views.logout_user, name = 'logout_user'),
        ]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

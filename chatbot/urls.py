from django.urls import path
from . import views

urlpatterns = [
    path('ask/', views.chat_endpoint, name='chat_endpoint'),
    path('api/chat/', views.chat_endpoint, name='chat_endpoint'),
]
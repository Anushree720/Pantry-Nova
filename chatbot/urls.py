from django.urls import path
from . import views


urlpatterns = [
    path('', views.chatbot, name='chatbot'),
    path('send/', views.chatbot_send, name='chatbot_send'),
    path('new/', views.chatbot_new, name='chatbot_new'),
    path('history/', views.chatbot_history, name='chatbot_history'),
]

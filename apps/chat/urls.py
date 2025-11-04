# apps/chat/urls.py
from django.urls import path
from .views import chat_messages_view

urlpatterns = [
    path('chat/<int:appointment_id>/messages/', chat_messages_view, name='chat-messages'),
]
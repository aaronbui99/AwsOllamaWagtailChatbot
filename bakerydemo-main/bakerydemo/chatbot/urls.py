from django.urls import path
from .views import chatbot_api, chatbot_ui

urlpatterns = [
    path("api/chatbot/", chatbot_api, name="chatbot_api"),
    path("chatbot/", chatbot_ui, name="chatbot_ui"),
]

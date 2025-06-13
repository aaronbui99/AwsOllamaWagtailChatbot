from django.urls import path
from .views import chatbot_api, chatbot_ui, test_ollama_connection

urlpatterns = [
    path("api/chatbot/", chatbot_api, name="chatbot_api"),
    path("chatbot/", chatbot_ui, name="chatbot_ui"),
    path("api/test-ollama/", test_ollama_connection, name="test_ollama_connection"),
]

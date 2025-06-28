from django.urls import path
from django.views.generic import TemplateView
from .views import chatbot_api, chatbot_ui, test_ollama_connection, test_bedrock_embeddings

urlpatterns = [
    path("api/chatbot/", chatbot_api, name="chatbot_api"),
    path("chatbot/", chatbot_ui, name="chatbot_ui"),
    path("api/test-ollama/", test_ollama_connection, name="test_ollama_connection"),
    path("api/test-bedrock-embeddings/", test_bedrock_embeddings, name="test_bedrock_embeddings"),
    path("test-bedrock/", TemplateView.as_view(template_name="chatbot/test_bedrock.html"), name="test_bedrock_ui"),
]

from django.shortcuts import render
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

OLLAMA_API_URL = "http://54.206.117.216:11434/api/chat"

@csrf_exempt
def chatbot_api(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_prompt = data.get("message", "")
        payload = {
            "model": "deepseek-r1:1.5b",
            "messages": [{"role": "user", "content": user_prompt}],
            "stream": False
        }
        response = requests.post(OLLAMA_API_URL, json=payload)
        return JsonResponse({
            "response": response.json().get("message", {}).get("content", "")
        })
    return JsonResponse({"error": "Only POST method allowed"}, status=405)

def chatbot_ui(request):
    return render(request, "chatbot/chatbot.html")

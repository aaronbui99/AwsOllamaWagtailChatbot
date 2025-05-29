import json
import requests
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .models import ChatLog

# Ollama endpoint, loaded from Django settings or fallback
OLLAMA_API_URL = getattr(settings, 'OLLAMA_API_URL', 'http://127.0.0.1:11434/api/generate')

@csrf_exempt
def chatbot_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)
    try:
        data = json.loads(request.body)
        user_prompt = data.get('message', '').strip()

        # Build the conversation array
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_prompt}
        ]

        # Call Ollama
        payload = {
            "model": "deepseek-r1:1.5b",
            "prompt": user_prompt,
            "stream": False
        }
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        result = response.json()
        ai_content = result.get('response', '')

        # Append AI response to messages
        messages.append({"role": "assistant", "content": ai_content})

        # Persist to AWS RDS via Django model
        ChatLog.objects.create(messages=messages)

        return JsonResponse({"response": ai_content})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def chatbot_ui(request):
    # Renders the chatbot interface
    return render(request, "chatbot/chatbot.html")

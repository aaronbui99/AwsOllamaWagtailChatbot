import json
import logging
import requests
import subprocess
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .models import ChatLog

# Set up logging
logger = logging.getLogger(__name__)

@csrf_exempt
def chatbot_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)
    try:
        # Log the Ollama API URL being used
        logger.info(f"Using Ollama API URL: {settings.OLLAMA_API_URL}")
        
        data = json.loads(request.body)
        user_prompt = data.get('message', '').strip()
        logger.info(f"Received user prompt: {user_prompt}")

        # Build the conversation array
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_prompt}
        ]

        # Call Ollama with the correct payload structure
        payload = {
            "model": "deepseek-r1:1.5b",
            "prompt": user_prompt,
            "stream": False
        }
        
        # Log the request payload and URL
        logger.info(f"Sending request to Ollama at URL: {settings.OLLAMA_API_URL}")
        
        # Use curl command directly since it works reliably in our tests
        try:
            # Escape double quotes in the prompt for the curl command
            escaped_prompt = user_prompt.replace('"', '\\"')
            
            # Construct the curl command
            curl_cmd = f'curl -s -X POST "{settings.OLLAMA_API_URL}" -H "Content-Type: application/json" -d "{{\\"model\\":\\"deepseek-r1:1.5b\\",\\"prompt\\":\\"{escaped_prompt}\\",\\"stream\\":false}}"'
            logger.info(f"Executing curl command: {curl_cmd}")
            
            # Execute the curl command
            result = subprocess.run(curl_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Curl command failed with return code {result.returncode}")
                if result.stderr:
                    logger.error(f"Curl error: {result.stderr}")
                raise Exception(f"Curl command failed: {result.stderr}")
            
            # Parse the JSON response
            try:
                response_data = json.loads(result.stdout)
                logger.info("Successfully parsed JSON response from curl command")
                ai_content = response_data.get('response', '')
                
                # Append AI response to messages
                messages.append({"role": "assistant", "content": ai_content})
                
                # Persist to AWS RDS via Django model
                ChatLog.objects.create(messages=messages)
                
                return JsonResponse({"response": ai_content})
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON response: {result.stdout}")
                raise Exception("Invalid JSON response from Ollama API")
                
        except Exception as e:
            logger.exception(f"Error using curl command: {str(e)}")
            
            # Fallback to using requests if curl fails
            logger.info("Falling back to requests library")
            try:
                headers = {'Content-Type': 'application/json'}
                response = requests.post(
                    settings.OLLAMA_API_URL, 
                    json=payload, 
                    headers=headers,
                    timeout=120  # Extended timeout
                )
                
                # Log the response status
                logger.info(f"Requests response status code: {response.status_code}")
                
                # Check if the response is successful
                response.raise_for_status()
                
                # Parse the JSON response
                result = response.json()
                logger.info("Successfully parsed JSON response from requests")
                ai_content = result.get('response', '')
                
                # Append AI response to messages
                messages.append({"role": "assistant", "content": ai_content})
                
                # Persist to AWS RDS via Django model
                ChatLog.objects.create(messages=messages)
                
                return JsonResponse({"response": ai_content})
                
            except requests.exceptions.Timeout:
                logger.error("Request to Ollama API timed out")
                return JsonResponse({"error": "Request to Ollama API timed out. Please try again later."}, status=504)
            except requests.exceptions.ConnectionError:
                logger.error(f"Connection error to Ollama API at {settings.OLLAMA_API_URL}")
                return JsonResponse({"error": f"Could not connect to Ollama API at {settings.OLLAMA_API_URL}. Please check if the service is running."}, status=503)
            except requests.exceptions.RequestException as req_err:
                logger.error(f"Request error: {str(req_err)}")
                return JsonResponse({"error": f"Request error: {str(req_err)}"}, status=500)
    
    except Exception as e:
        logger.exception(f"Unexpected error in chatbot_api: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)
            
        # Log the raw response for debugging
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {response.headers}")
        
        # Check if the response is valid JSON
        try:
            result = response.json()
            logger.info(f"Received JSON response from Ollama: {result}")
            ai_content = result.get('response', '')
            
            # If response is empty, log the raw text
            if not ai_content:
                logger.warning(f"Empty AI content. Raw response text: {response.text}")
                ai_content = "Sorry, I couldn't generate a response. Please try again."
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON response. Raw response: {response.text}")
            raise Exception("Invalid JSON response from Ollama API")
        
        # Append AI response to messages
        messages.append({"role": "assistant", "content": ai_content})
        
        # Persist to AWS RDS via Django model
        ChatLog.objects.create(messages=messages)
        
        return JsonResponse({"response": ai_content})
        
    except requests.exceptions.Timeout:
        logger.error("Request to Ollama API timed out")
        return JsonResponse({"error": "Request to Ollama API timed out. Please try again later."}, status=504)
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error to Ollama API at {settings.OLLAMA_API_URL}")
        return JsonResponse({"error": f"Could not connect to Ollama API at {settings.OLLAMA_API_URL}. Please check if the service is running."}, status=503)
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Request error: {str(req_err)}")
        return JsonResponse({"error": f"Request error: {str(req_err)}"}, status=500)

    except Exception as e:
        logger.exception(f"Unexpected error in chatbot_api: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


def chatbot_ui(request):
    # Renders the chatbot interface
    return render(request, "chatbot/chatbot.html")

@csrf_exempt
def test_ollama_connection(request):
    """
    A simple endpoint to test the connection to the Ollama API
    """
    try:
        logger.info(f"Testing connection to Ollama API at: {settings.OLLAMA_API_URL}")
        
        # Try using curl first (which we know works from our tests)
        try:
            curl_cmd = f'curl -s -X POST "{settings.OLLAMA_API_URL}" -H "Content-Type: application/json" -d "{{\\"model\\":\\"deepseek-r1:1.5b\\",\\"prompt\\":\\"Hello, testing the connection!\\",\\"stream\\":false}}"'
            logger.info(f"Testing with curl command: {curl_cmd}")
            
            result = subprocess.run(curl_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Curl command failed with return code {result.returncode}")
                if result.stderr:
                    logger.error(f"Curl error: {result.stderr}")
                raise Exception(f"Curl command failed: {result.stderr}")
            
            # Try to parse the response as JSON
            try:
                response_data = json.loads(result.stdout)
                logger.info(f"Curl response JSON: {response_data}")
                
                return JsonResponse({
                    "status": "success",
                    "method": "curl",
                    "message": "Successfully connected to Ollama API using curl",
                    "api_url": settings.OLLAMA_API_URL,
                    "response": response_data
                })
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON response from curl. Raw response: {result.stdout}")
                raise Exception("Invalid JSON response from curl command")
                
        except Exception as curl_error:
            logger.warning(f"Curl method failed: {str(curl_error)}. Trying requests library...")
            
            # Fallback to using requests
            # Simple test payload
            payload = {
                "model": "deepseek-r1:1.5b",
                "prompt": "Hello, testing the connection!",
                "stream": False
            }
            
            # Make the request
            response = requests.post(
                settings.OLLAMA_API_URL, 
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30  # Increased timeout
            )
            
            # Log the response details
            logger.info(f"Requests response status code: {response.status_code}")
            logger.info(f"Requests response headers: {response.headers}")
            
            # Try to parse the response as JSON
            try:
                result = response.json()
                logger.info(f"Requests response JSON: {result}")
                return JsonResponse({
                    "status": "success",
                    "method": "requests",
                    "message": "Successfully connected to Ollama API using requests",
                    "api_url": settings.OLLAMA_API_URL,
                    "response": result
                })
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON response. Raw response: {response.text}")
                return JsonResponse({
                    "status": "error",
                    "message": "Connected to API but received invalid JSON response",
                    "api_url": settings.OLLAMA_API_URL,
                    "raw_response": response.text
                }, status=500)
            
    except requests.exceptions.Timeout:
        logger.error("Connection to Ollama API timed out")
        return JsonResponse({
            "status": "error",
            "message": "Connection to Ollama API timed out",
            "api_url": settings.OLLAMA_API_URL
        }, status=504)
    except requests.exceptions.ConnectionError:
        logger.error(f"Failed to connect to Ollama API at {settings.OLLAMA_API_URL}")
        return JsonResponse({
            "status": "error",
            "message": f"Failed to connect to Ollama API at {settings.OLLAMA_API_URL}",
            "api_url": settings.OLLAMA_API_URL
        }, status=503)
    except Exception as e:
        logger.exception(f"Unexpected error testing Ollama connection: {str(e)}")
        return JsonResponse({
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "api_url": settings.OLLAMA_API_URL
        }, status=500)

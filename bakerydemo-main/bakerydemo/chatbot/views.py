import json
import logging
import os
import requests
import subprocess
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .models import ChatLog
from .bedrock_embeddings import BedrockEmbeddings

# Set up logging
logger = logging.getLogger(__name__)

@csrf_exempt
def chatbot_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)
    try:
        # Make sure we have a session key for anonymous users
        if not request.session.session_key:
            request.session.save()
            
        # Log the Ollama API URL being used
        logger.info(f"Using Ollama API URL: {settings.OLLAMA_API_URL}")
        
        data = json.loads(request.body)
        user_prompt = data.get('message', '').strip()
        use_bedrock_embeddings = data.get('use_bedrock_embeddings', True)
        logger.info(f"Received user prompt: {user_prompt}")
        
        # If Bedrock embeddings are enabled, generate embeddings for the user prompt
        if use_bedrock_embeddings:
            try:
                # Initialize Bedrock embeddings
                bedrock_embeddings = BedrockEmbeddings()
                 
                # Generate embeddings for the user prompt
                embeddings = bedrock_embeddings.embed_query(user_prompt)
                
                # Log success
                logger.info(f"Successfully generated Bedrock embeddings for user prompt. Vector length: {len(embeddings)}")
                
                # Store embeddings for later use (e.g., for RAG)
                # This could be stored in the session, database, or passed to another service
                request.session['last_prompt_embeddings'] = embeddings
                
            except Exception as e:
                logger.error(f"Error generating Bedrock embeddings: {str(e)}")
                # Continue with the chatbot flow even if embeddings generation fails

        # Build the conversation array
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_prompt}
        ]

        # Call Ollama with the correct payload structure
        model_name = "deepseek-bakery-expert"
        payload = {
            "model": model_name,
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
            curl_cmd = f'curl -s -X POST "{settings.OLLAMA_API_URL}" -H "Content-Type: application/json" -d "{{\\"model\\":\\"{model_name}\\",\\"prompt\\":\\"{escaped_prompt}\\",\\"stream\\":false}}"'
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
                chat_log = ChatLog.objects.create(
                    messages=messages,
                    model_name=model_name,
                    user=request.user if request.user.is_authenticated else None,
                    session_key=request.session.session_key
                )
                
                # Include information about embeddings in the response
                response_data = {
                    "response": ai_content,
                    "embeddings_generated": use_bedrock_embeddings
                }
                
                # If embeddings were generated, include the vector length
                if use_bedrock_embeddings and 'last_prompt_embeddings' in request.session:
                    response_data["embeddings_length"] = len(request.session['last_prompt_embeddings'])
                
                return JsonResponse(response_data)
                
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
                chat_log = ChatLog.objects.create(
                    messages=messages,
                    model_name=model_name,
                    user=request.user if request.user.is_authenticated else None,
                    session_key=request.session.session_key
                )
                
                # Include information about embeddings in the response
                response_data = {
                    "response": ai_content,
                    "embeddings_generated": use_bedrock_embeddings
                }
                
                # If embeddings were generated, include the vector length
                if use_bedrock_embeddings and 'last_prompt_embeddings' in request.session:
                    response_data["embeddings_length"] = len(request.session['last_prompt_embeddings'])
                
                return JsonResponse(response_data)
                
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
        # Make sure we have a session key for anonymous users
        if not request.session.session_key:
            request.session.save()
            
        logger.info(f"Testing connection to Ollama API at: {settings.OLLAMA_API_URL}")
        
        # Test prompt and model
        test_prompt = "Hello, testing the connection!"
        model_name = "deepseek-bakery-expert"
        
        # Build the conversation array for logging
        messages = [
            {"role": "system", "content": "Connection test."},
            {"role": "user", "content": test_prompt}
        ]
        
        # Try using curl first (which we know works from our tests)
        try:
            curl_cmd = f'curl -s -X POST "{settings.OLLAMA_API_URL}" -H "Content-Type: application/json" -d "{{\\"model\\":\\"{model_name}\\",\\"prompt\\":\\"{test_prompt}\\",\\"stream\\":false}}"'
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
                
                # Get the AI response
                ai_content = response_data.get('response', '')
                
                # Append AI response to messages
                messages.append({"role": "assistant", "content": ai_content})
                
                # Store the test in the database
                chat_log = ChatLog.objects.create(
                    messages=messages,
                    model_name=model_name,
                    user=request.user if request.user.is_authenticated else None,
                    session_key=request.session.session_key,
                    user_prompt=test_prompt,
                    ai_response=ai_content
                )
                
                return JsonResponse({
                    "status": "success",
                    "method": "curl",
                    "message": "Successfully connected to Ollama API using curl",
                    "api_url": settings.OLLAMA_API_URL,
                    "response": response_data,
                    "chat_log_id": chat_log.id
                })
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON response from curl. Raw response: {result.stdout}")
                raise Exception("Invalid JSON response from curl command")
                
        except Exception as curl_error:
            logger.warning(f"Curl method failed: {str(curl_error)}. Trying requests library...")
            
            # Fallback to using requests
            # Simple test payload
            payload = {
                "model": model_name,
                "prompt": test_prompt,
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
                
                # Get the AI response
                ai_content = result.get('response', '')
                
                # Append AI response to messages
                messages.append({"role": "assistant", "content": ai_content})
                
                # Store the test in the database
                chat_log = ChatLog.objects.create(
                    messages=messages,
                    model_name=model_name,
                    user=request.user if request.user.is_authenticated else None,
                    session_key=request.session.session_key,
                    user_prompt=test_prompt,
                    ai_response=ai_content
                )
                
                return JsonResponse({
                    "status": "success",
                    "method": "requests",
                    "message": "Successfully connected to Ollama API using requests",
                    "api_url": settings.OLLAMA_API_URL,
                    "response": result,
                    "chat_log_id": chat_log.id
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

@csrf_exempt
def test_bedrock_embeddings(request):
    """
    A simple endpoint to test the connection to AWS Bedrock and generate embeddings
    """
    try:
        # Parse request data
        if request.method == 'POST':
            data = json.loads(request.body)
            test_text = data.get('text', 'Hello, testing AWS Bedrock embeddings!')
        else:
            test_text = "Hello, testing AWS Bedrock embeddings!"
        
        logger.info(f"Testing AWS Bedrock embeddings with text: '{test_text}'")
        
        # Log AWS environment variables (without sensitive values)
        logger.info(f"AWS_REGION: {os.environ.get('AWS_REGION', 'Not set')}")
        logger.info(f"AWS_ACCESS_KEY_ID: {'Set' if os.environ.get('AWS_ACCESS_KEY_ID') else 'Not set'}")
        logger.info(f"AWS_SECRET_ACCESS_KEY: {'Set' if os.environ.get('AWS_SECRET_ACCESS_KEY') else 'Not set'}")
        
        try:
            # Initialize Bedrock embeddings
            from .bedrock_embeddings import BedrockEmbeddings
            logger.info("Initializing BedrockEmbeddings class")
            bedrock_embeddings = BedrockEmbeddings()
            
            # Generate embeddings
            logger.info("Calling embed_query method")
            embedding_vector = bedrock_embeddings.embed_query(test_text)
            
            logger.info(f"Successfully generated embeddings with length: {len(embedding_vector)}")
            
            # Return success response
            return JsonResponse({
                "status": "success",
                "message": "Successfully generated embeddings using AWS Bedrock",
                "text": test_text,
                "embedding_length": len(embedding_vector),
                "embedding_sample": embedding_vector[:5]  # Return first 5 values as a sample
            })
            
        except Exception as e:
            logger.exception(f"Error generating embeddings: {str(e)}")
            
            # Get more detailed error information
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"Detailed error traceback: {error_traceback}")
            
            return JsonResponse({
                "status": "error",
                "message": f"Error generating embeddings: {str(e)}",
                "text": test_text,
                "traceback": error_traceback
            }, status=500)
            
    except Exception as e:
        logger.exception(f"Unexpected error testing Bedrock embeddings: {str(e)}")
        return JsonResponse({
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }, status=500)

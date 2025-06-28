#!/usr/bin/env python
"""
Test script to verify connection to the Ollama API
"""
import os
import json
import requests
import subprocess
import time

# The Ollama API URL to test
OLLAMA_API_URL = "http://ec2-3-106-117-22.ap-southeast-2.compute.amazonaws.com:11434/api/generate"

def test_with_requests():
    """Test connection using the requests library"""
    print(f"\n=== Testing connection to {OLLAMA_API_URL} using requests ===")
    
    payload = {
        "model": "deepseek-r1:1.5b",
        "prompt": "Hello, testing the connection!",
        "stream": False
    }
    
    headers = {'Content-Type': 'application/json'}
    
    try:
        print("Sending request...")
        start_time = time.time()
        response = requests.post(
            OLLAMA_API_URL,
            json=payload,
            headers=headers,
            timeout=60
        )
        elapsed_time = time.time() - start_time
        
        print(f"Request completed in {elapsed_time:.2f} seconds")
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"Response JSON: {json.dumps(result, indent=2)}")
                return True
            except json.JSONDecodeError:
                print(f"Failed to decode JSON response. Raw response: {response.text}")
                return False
        else:
            print(f"Request failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("Connection timed out")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {str(e)}")
        return False
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return False

def test_with_curl():
    """Test connection using curl command"""
    print(f"\n=== Testing connection to {OLLAMA_API_URL} using curl ===")
    
    curl_cmd = f'curl -v -X POST "{OLLAMA_API_URL}" -H "Content-Type: application/json" -d "{{\\"model\\":\\"deepseek-r1:1.5b\\",\\"prompt\\":\\"Hello, testing the connection!\\",\\"stream\\":false}}"'
    
    print(f"Running command: {curl_cmd}")
    
    try:
        start_time = time.time()
        result = subprocess.run(curl_cmd, shell=True, capture_output=True, text=True)
        elapsed_time = time.time() - start_time
        
        print(f"Command completed in {elapsed_time:.2f} seconds")
        
        if result.stdout:
            print(f"Output: {result.stdout}")
            try:
                json_result = json.loads(result.stdout)
                print(f"Parsed JSON: {json.dumps(json_result, indent=2)}")
                return True
            except json.JSONDecodeError:
                print("Failed to parse output as JSON")
                return False
        
        if result.stderr:
            print(f"Error: {result.stderr}")
            return False
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error running curl command: {str(e)}")
        return False

def test_ping():
    """Test basic connectivity to the host with ping"""
    print("\n=== Testing basic connectivity with ping ===")
    
    # Extract hostname from URL
    import re
    hostname_match = re.search(r'http://([^:/]+)', OLLAMA_API_URL)
    if not hostname_match:
        print(f"Could not extract hostname from URL: {OLLAMA_API_URL}")
        return False
        
    hostname = hostname_match.group(1)
    print(f"Pinging {hostname}...")
    
    ping_cmd = f"ping -n 4 {hostname}"
    
    try:
        result = subprocess.run(ping_cmd, shell=True, capture_output=True, text=True)
        print(result.stdout)
        
        if "Request timed out" in result.stdout or "100% loss" in result.stdout:
            print("Ping failed - host is unreachable")
            return False
        else:
            print("Ping successful - host is reachable")
            return True
            
    except Exception as e:
        print(f"Error running ping command: {str(e)}")
        return False

def test_telnet():
    """Test if the port is open using telnet-like functionality"""
    print("\n=== Testing port connectivity ===")
    
    import re
    import socket
    
    # Extract hostname and port from URL
    url_match = re.search(r'http://([^:]+):(\d+)', OLLAMA_API_URL)
    if not url_match:
        print(f"Could not extract hostname and port from URL: {OLLAMA_API_URL}")
        return False
        
    hostname = url_match.group(1)
    port = int(url_match.group(2))
    
    print(f"Testing connection to {hostname}:{port}...")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    
    try:
        result = sock.connect_ex((hostname, port))
        if result == 0:
            print(f"Port {port} is open on {hostname}")
            return True
        else:
            print(f"Port {port} is closed on {hostname}")
            return False
    except socket.gaierror:
        print(f"Could not resolve hostname: {hostname}")
        return False
    except socket.timeout:
        print(f"Connection to {hostname}:{port} timed out")
        return False
    except Exception as e:
        print(f"Error testing port connectivity: {str(e)}")
        return False
    finally:
        sock.close()

if __name__ == "__main__":
    print("=== Ollama API Connection Test ===")
    print(f"Testing connection to: {OLLAMA_API_URL}")
    
    # Run all tests
    ping_result = test_ping()
    telnet_result = test_telnet()
    curl_result = test_with_curl()
    requests_result = test_with_requests()
    
    # Summary
    print("\n=== Test Summary ===")
    print(f"Ping test: {'PASSED' if ping_result else 'FAILED'}")
    print(f"Port connectivity test: {'PASSED' if telnet_result else 'FAILED'}")
    print(f"Curl test: {'PASSED' if curl_result else 'FAILED'}")
    print(f"Requests test: {'PASSED' if requests_result else 'FAILED'}")
    
    if ping_result and not telnet_result:
        print("\nDIAGNOSIS: The host is reachable but the port is closed or blocked by a firewall.")
        print("SOLUTION: Ensure the Ollama service is running on the EC2 instance and the port is open in the security group.")
    elif not ping_result:
        print("\nDIAGNOSIS: The host is unreachable.")
        print("SOLUTION: Check if the EC2 instance is running and has a public IP address.")
    elif telnet_result and not (curl_result or requests_result):
        print("\nDIAGNOSIS: The port is open but the Ollama API is not responding correctly.")
        print("SOLUTION: Check if the Ollama service is running properly on the EC2 instance.")
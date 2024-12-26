import os
import random
from typing import Dict, Generator, Tuple
import requests
import base64

API_URL = os.getenv("API_URL")

def update_file_metadata(filename: str, update_dict: dict, access_token: str) -> int:
    """
    Updates the weight of a specific file via a POST request to the API.
    
    Args:
    - filename (str): The name of the file to update.
    - new_weight (int): The new weight to be assigned to the file.
    - access_token (str): Bearer token for authorization.
    
    Returns:
    - int: The HTTP status code of the response.
    """
    url = f"{API_URL}/api/v1/files/{filename}/metadata"
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    response = requests.post(url, headers=headers, json=update_dict)
    print(response.text)
    return response.status_code


def fetch_files_metadata(access_token: str) -> Tuple[Dict[str, int], int]:
    """
    Fetches files metadata from the API and returns a dictionary with filenames as keys and weights as values.
    
    Args:
    - api_url (str): The base URL of the API.
    - access_token (str): Bearer token for authorization.
    
    Returns:
    - Tuple[Dict[str, int], int]: A tuple containing the dictionary of filenames and weights, and the HTTP status code.
    """
    url = f"{API_URL}/api/v1/files/metadata"
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, headers=headers)
    response_data = response.json()

    # Extracting filenames and their corresponding weights into a dictionary
    files_metadata = {item['filename']: item['metadata'] for item in response_data.get('metadatas', [])}
    print(response.text)
    return files_metadata, response.status_code

def evaluate_scenario(scenario_name: str, scenario_description: str, scenario_text: str,
                      best_response: str, explanation: str, difficulty: str, importance: str,
                      salesman_response: str, access_token: str):
    """Evaluate a response for a given scenario."""
    url = f"{API_URL}/api/v1/scenarios/evaluate_scenario"
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    data = {
        "scenario": {
            "name": scenario_name,
            "description": scenario_description,
            "scenario": scenario_text,
            "best_response": best_response,
            "explanation": explanation,
            "difficulty": difficulty,
            "importance": importance
        },
        "salesman_response": salesman_response
    }
    response = requests.post(url, json=data, headers=headers)
    return response.json(), response.status_code

def generate_scenario(scenario_name: str, access_token: str):
    """Generate a scenario based on a scenario name."""
    url = f"{API_URL}/api/v1/scenarios/generate_scenario"
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    data = {'scenario_name': scenario_name}
    response = requests.post(url, json=data, headers=headers, stream=True)
    if response.status_code == 200:
        for line in response.iter_content(decode_unicode=True, chunk_size=10):
            if line:
                decoded_line = line.decode('utf-8', errors="ignore") if isinstance(line, bytes) else line
                print(type(decoded_line), type(line))
                yield decoded_line
    else:
        yield f"Failed to get response from AI: {response.status_code}"
        
def generate_scenario_metadata(scenario: str, access_token: str):
    """Generate a scenario based on a scenario name."""
    url = f"{API_URL}/api/v1/scenarios/generate_scenario_metadata"
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    data = {'scenario': scenario}
    response = requests.post(url, json=data, headers=headers)
    return response
           
def add_scenario(name: str, prompt: str, file_names: list[str], access_token: str):
    """Add a new scenario."""
    url = f"{API_URL}/api/v1/scenarios/add_scenario"
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    data = {
        'name': name,
        'prompt': prompt,
        'file_names': file_names
    }
    response = requests.post(url, json=data, headers=headers)
    return response.json(), response.status_code

def get_scenario(name: str, access_token: str):
    """Get a scenario by name."""
    url = f"{API_URL}/api/v1/scenarios/get_scenario/{name}"
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, headers=headers)
    return response.json(), response.status_code

def update_scenario(name: str, attributes: dict, access_token: str):
    """Update an existing scenario."""
    url = f"{API_URL}/api/v1/scenarios/update_scenario/{name}"
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    response = requests.put(url, json=attributes, headers=headers)
    return response.json(), response.status_code

def get_all_scenarios(access_token: str):
    """Get all scenarios."""
    url = f"{API_URL}/api/v1/scenarios/get_all_scenarios"
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, headers=headers)
    return response.json(), response.status_code

def delete_scenario(name: str, access_token: str):
    """Delete a scenario by name."""
    url = f"{API_URL}/api/v1/scenarios/delete_scenario/{name}"
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.delete(url, headers=headers)
    return response.json(), response.status_code

def generate_response(question: str, access_token: str, role: str):
    """Generate a response using the chat API."""
    url = f"{API_URL}/api/v1/chat-stream"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    data = {
        'question': question,
        'chat_history': [],
        'get_highest_ranking_response': False,
        'temperature': int(random.randrange(0,1)) /10,
        "role" : role
    }
    response = requests.post(url, json=data, headers=headers)
    print(response.text)
    return response.json(), response.status_code

def get_roles(access_token: str):
    """Retrieve all roles."""
    url = f'{API_URL}/api/v1/roles/all'
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, headers=headers, allow_redirects=True)
    return response.json()['roles'] if response.status_code == 200 else []

def add_role(name: str, prompt_prefix: str, access_token: str):
    """Add a new role with a prompt prefix."""
    url = f'{API_URL}/api/v1/roles/new'
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    data = {'name': name, 'prompt': prompt_prefix}
    response = requests.post(url, headers=headers, json=data)
    print(response.text)
    return response.status_code == 200

def update_role(name: str, new_prompt_prefix: str, access_token: str):
    """Update the prompt prefix for a role."""
    url = f'{API_URL}/api/v1/roles/{name}'
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    data = {'prompt_prefix': new_prompt_prefix}
    response = requests.put(url, headers=headers, json=data)
    return response.status_code == 200

def delete_role(name: str, access_token: str):
    """Delete a role."""
    url = f'{API_URL}/api/v1/roles/{name}'
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.delete(url, headers=headers)
    return response.status_code == 200

def get_chat_response_stream(question: str, chat_history: list, access_token: str, role: str) -> Generator[str, None, None]:
    """Send a question to the AI chat API and receive a streaming response."""
    url = f'{API_URL}/api/v1/chat/chat-stream'
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    data = {
        'question': question,
        'chat_history': chat_history,
        'get_highest_ranking_response': True,
        'role': role
    }

    response = requests.post(url, headers=headers, json=data, stream=True)
    
    if response.status_code == 200:
        for line in response.iter_content(decode_unicode=True, chunk_size=10):
            if line:
                decoded_line = line.decode('utf-8') if isinstance(line, bytes) else line
                print(type(decoded_line), type(line))
                yield decoded_line
    else:
        yield f"Failed to get response from AI: {response.status_code}"

def get_files(access_token: str):
    """Retrieve list of files."""
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(f'{API_URL}/api/v1/files/all', headers=headers)
    return response.json() if response.status_code == 200 else []

def delete_file(file_name: str, access_token: str):
    """Delete a file."""
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.delete(f'{API_URL}/api/v1/files/{file_name}', headers=headers)
    print(response.text)
    return response.status_code == 200

def upload_file(file_name: str, file_data: bytes, description: str, weight: int, role: str, access_token: str) -> bool:
    """Upload a file, extracting the file extension automatically."""
    # Extracting file extension
    _, file_extension = os.path.splitext(file_name)
    
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    encoded_file = base64.b64encode(file_data).decode('utf-8')
    data = {
        'file': encoded_file,
        'description': description,
        'extension': file_extension,  # Use the extracted extension,
        'weight' : weight,
        "role" : role
    }
    
    response = requests.post(f'{API_URL}/api/v1/files/ingest?file_name={file_name}', headers=headers, json=data)
    print(response.text)
    return response.status_code == 200

def get_access_token(email: str, password: str) -> str:
    """
    Retrieve access token from the authentication server.
    
    Args:
    - email (str): User's email address
    - password (str): User's password
    
    Returns:
    - str: Access token if authentication is successful
    
    Raises:
    - Exception: If authentication fails
    """
    url = 'https://api.themark.academy/backend/api/user/userLogin'
    data = {
        'email': email,
        'password': password
    }
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        response_data = response.json()
        if response_data.get('success'):
            return response_data['data']['token']
        else:
            raise Exception(response_data.get('message', 'Authentication failed'))
    else:
        raise Exception(f"Failed to retrieve access token. Status code: {response.status_code}")

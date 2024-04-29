import os
import requests
import base64

API_URL = 'http://146.190.14.15'


def get_roles(access_token: str):
    """Retrieve all roles."""
    url = f'{API_URL}/api/v1/roles/'
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, headers=headers)
    return response.json()['roles'] if response.status_code == 200 else []

def add_role(name: str, prompt_prefix: str, access_token: str):
    """Add a new role with a prompt prefix."""
    url = f'{API_URL}/api/v1/roles/'
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    data = {'name': name, 'prompt': prompt_prefix}
    response = requests.post(url, headers=headers, json=data)
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




def get_chat_response(question: str, chat_history: list, access_token: str) -> str:
    """Send a question to the AI chat API and receive a response."""
    url = f'{API_URL}/api/v1/chat'
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    data = {
        'question': question,
        'chat_history': chat_history,
        'get_highest_ranking_response': True,
        'temperature': 0
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['ai_response']
    else:
        return "Failed to get response from AI."




def get_files(access_token: str):
    """Retrieve list of files."""
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(f'{API_URL}/api/v1/files', headers=headers)
    return response.json() if response.status_code == 200 else []

def delete_file(file_name: str, access_token: str):
    """Delete a file."""
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.delete(f'{API_URL}/api/v1/files/{file_name}', headers=headers)
    return response.status_code == 200

def upload_file(file_name: str, file_data: bytes, description: str, access_token: str) -> bool:
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
        'extension': file_extension  # Use the extracted extension
    }
    
    response = requests.post(f'{API_URL}/api/v1/injest_data?file_name={file_name}', headers=headers, json=data)
    return response.status_code == 200


def list_prompts(access_token: str):
    """List all prompts."""
    url = f'{API_URL}/api/v1/prompts/list_prompts'
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.post(url, headers=headers)
    print(response.text)
    if response.status_code == 200:
        return response.json()['prompts']
    else:
        return []

def delete_prompt(prompt_name: str, access_token: str):
    """Delete a prompt."""
    url = f'{API_URL}/api/v1/prompts/delete_prompt/{prompt_name}'
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.delete(url, headers=headers)
    print(response.text)
    return response.status_code == 200, response.json()

def choose_main_prompt(prompt_name: str, access_token: str):
    """Set a prompt as the main prompt."""
    url = f'{API_URL}/api/v1/prompts/choose_main_prompt'
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    data = {'name': prompt_name}
    response = requests.post(url, headers=headers, json=data)
    print(response.text)
    return response.status_code == 200, response.json()

def update_prompt(prompt_name: str, new_content: str, access_token: str):
    """Update a prompt."""
    url = f'{API_URL}/api/v1/prompts/update_prompt/{prompt_name}'
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    data = {'content': new_content}
    response = requests.post(url, headers=headers, json=data)
    print(response.text)
    return response.status_code == 200, response.json()


def create_prompt(name: str, content: str, is_main: bool, access_token: str) -> bool:
    """Create a new prompt."""
    url = f'{API_URL}/api/v1/prompts/create_prompt'
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    data = {
        'name': name,
        'prompt': content,
        'is_main': is_main
    }
    response = requests.post(url, headers=headers, json=data)
    print(response.text)
    return response.status_code == 200, response.json()

def get_access_token(username: str, password: str, client_id: str = '', client_secret: str = '') -> str:
    """Retrieve access token from the authentication server."""
    url = f'{API_URL}/token'
    data = {
        'grant_type': 'password',
        'username': username,
        'password': password,
        'client_id': client_id,
        'client_secret': client_secret
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.post(url, data=data, headers=headers)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception("Failed to retrieve access token")

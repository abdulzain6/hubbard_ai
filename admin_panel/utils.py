import os
import requests
import base64

API_URL = 'http://146.190.14.15'

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

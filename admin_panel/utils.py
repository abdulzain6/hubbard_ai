import os
import requests
import base64

API_URL = 'http://146.190.14.15'

def get_all_scenarios(access_token: str):
    """Fetch all scenarios from the API."""
    url = f"{API_URL}/api/v1/scenarios/get_all_scenarios"
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, headers=headers)
    return response.json(), response.status_code

def create_scenario(data: dict, access_token: str):
    """Create a new scenario."""
    url = f"{API_URL}/api/v1/scenarios/create_scenario"
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    response = requests.post(url, json=data, headers=headers)
    return response.json(), response.status_code

def update_scenario(scenario_name: str, data: dict, access_token: str):
    """Update an existing scenario."""
    url = f"{API_URL}/api/v1/scenarios/update_scenario/{scenario_name}"
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    response = requests.put(url, json=data, headers=headers)
    return response.json(), response.status_code

def delete_scenario(scenario_name: str, access_token: str):
    """Delete a scenario."""
    url = f"{API_URL}/api/v1/scenarios/delete_scenario/{scenario_name}"
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.delete(url, headers=headers)
    return response.json(), response.status_code

def evaluate_scenario(scenario_name: str, salesman_response: str, access_token: str):
    """Evaluate a response for a given scenario."""
    url = f"{API_URL}/api/v1/scenarios/evaluate_scenario"
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    data = {
        'scenario_name': scenario_name,
        'salesman_response': salesman_response
    }
    response = requests.post(url, json=data, headers=headers)
    return response.json(), response.status_code

def generate_scenario(theme: str, access_token: str):
    """Generate a scenario based on a theme."""
    url = f"{API_URL}/api/v1/scenarios/generate_scenario"
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    data = {'theme': theme}
    response = requests.post(url, json=data, headers=headers)
    return response.json(), response.status_code



def set_rank(prompt: str, rank: int, from_rank: int, access_token: str):
    """Change the rank of a response."""
    url = f"{API_URL}/api/v1/responses/set_rank"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    data = {
        'prompt': prompt,
        'rank': rank,
        'from_rank': from_rank
    }
    response = requests.post(url, json=data, headers=headers)
    return response.json(), response.status_code

def generate_response(question: str, access_token: str):
    """Generate a response using the chat API."""
    url = f"{API_URL}/api/v1/chat"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    data = {
        'question': question,
        'chat_history': [],
        'get_highest_ranking_response': False
    }
    response = requests.post(url, json=data, headers=headers)
    print(response.text)
    return response.json(), response.status_code


def create_response(prompt: str, response: str, access_token: str):
    """Create a new response."""
    url = f"{API_URL}/api/v1/responses/create_response"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    data = {
        'prompt': prompt,
        'response': response
    }
    response = requests.post(url, json=data, headers=headers)
    return response.json(), response.status_code

def update_response(prompt: str, rank: int, new_response: str, rank_new: int, access_token: str):
    """Update an existing response."""
    url = f"{API_URL}/api/v1/responses/update_response"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    data = {
        'prompt': prompt,
        'rank': rank,
        'attributes': {'response': new_response, "rank" : rank_new}
    }
    response = requests.put(url, json=data, headers=headers)
    return response.json(), response.status_code

def delete_response(prompt: str, rank: int, access_token: str):
    """Delete a response."""
    url = f"{API_URL}/api/v1/responses/delete_response/{prompt}/{rank}"
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.delete(url, headers=headers)
    print(response.text)
    try:
        res = response.json()
    except:
        res = response.text
    return res, response.status_code

def list_responses(access_token: str, prompt: str):
    """List all responses."""
    url = f"{API_URL}/api/v1/responses/responses/{prompt}"
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, headers=headers)
    print(response.json())
    return response.json(), response.status_code

def register_admin(email: str, password: str, name: str, country: str, phone: str, company_role: str, company: str, department: str, access_token: str):
    """Register a new admin."""
    url = f'{API_URL}/api/v1/users/register_admin'
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    data = {
        'email': email,
        'password': password,
        'name': name,
        'country': country,
        'phone': phone,
        'company_role': company_role,
        'company': company,
        'department': department
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json(), response.status_code

def delete_user(email: str, access_token: str):
    """Delete a user."""
    url = f'{API_URL}/api/v1/users/delete_user/{email}'
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.delete(url, headers=headers)
    return response.json(), response.status_code

def update_user(email: str, updates: dict, access_token: str):
    """Update user details."""
    url = f'{API_URL}/api/v1/users/update_user/{email}'
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    response = requests.post(url, headers=headers, json=updates)
    return response.json(), response.status_code

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

def upload_file(file_name: str, file_data: bytes, description: str, weight: int, access_token: str) -> bool:
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
        'weight' : weight
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

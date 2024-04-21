import requests
import base64
import os
import json

def get_access_token(url, username, password, client_id='', client_secret=''):
    """Retrieve access token from the authentication server."""
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
    response = requests.post(f'{url}/token', data=data, headers=headers)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception("Failed to retrieve access token")

def encode_file_to_base64(file_path):
    """Encode file content to base64."""
    with open(file_path, 'rb') as file:
        return base64.b64encode(file.read()).decode('utf-8')

def ingest_data(url, token, file_name, file_content, description=''):
    """Send file data to the API."""
    data = {
        'text': '',  # Assuming 'text' is needed but empty
        'file': file_content,
        'description': description
    }
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'accept': 'application/json'
    }
    response = requests.post(f'{url}/api/v1/injest_data?file_name={file_name}', headers=headers, json=data)
    return response.json()

def main():
    # Configuration variables
    url = 'http://146.190.14.15'
    username = 'abdulzain6@gmail.com'
    password = 'zainZain123'
    file_path = '/home/zain/work/hubbard_ai_upload_files/Hubbard.ai Training Content/Duplicate Books/You Can_t Teach a Kid to Ride a Bike at a Seminar.pdf'
    
    # Get the access token
    token = get_access_token(url, username, password)

    # Encode the file
    file_content = encode_file_to_base64(file_path)

    # Upload the file
    file_name = os.path.basename(file_path)
    response = ingest_data(url, token, file_name, file_content)
    print(response)

if __name__ == "__main__":
    main()

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

def upload_files(folder_path: str, url: str):
    """Upload all files in a folder and keep track of uploaded files."""
    uploaded_files_path = os.path.join(folder_path, 'uploaded_files.txt')
    try:
        with open(uploaded_files_path, 'r') as file:
            uploaded_files = set(file.read().split(sep="\n"))
    except FileNotFoundError:
        uploaded_files = set()
    
    print(uploaded_files)

    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path) and file_name not in uploaded_files:
            print("Uploading ", file_name)
            file_content = encode_file_to_base64(file_path)
            response = ingest_data(url, get_access_token(url, 'abdulzain6@gmail.com', 'zainZain123'), file_name, file_content)
            print(response)
            # Update the tracking file
            with open(uploaded_files_path, 'a') as file:
                file.write(file_name + '\n')
                
def main():
    # Configuration variables
    url = 'http://146.190.14.15'
    file_path = '/home/zain/work/hubbard_ai_upload_files/Hubbard.ai Training Content/Duplicate Books'
    upload_files(file_path, url)


if __name__ == "__main__":
    main()

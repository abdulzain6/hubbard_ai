import requests

API_URL = 'http://146.190.14.15'

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

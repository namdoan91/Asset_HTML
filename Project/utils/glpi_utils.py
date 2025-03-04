import requests

def get_session_token(glpi_url, user_token, app_token):
    headers = {'Content-Type': 'application/json', 'Authorization': f'user_token {user_token}', 'App-Token': app_token}
    response = requests.get(f"{glpi_url}/initSession", headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()['session_token']

def fetch_computer_data(session_token, glpi_url, computer_id):
    headers = {'Content-Type': 'application/json', 'Session-Token': session_token, 'App-Token': app_token}
    response = requests.get(f"{glpi_url}/Computer/{computer_id}", headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()

def fetch_model_data(session_token, glpi_url, model_id):
    headers = {'Content-Type': 'application/json', 'Session-Token': session_token, 'App-Token': app_token}
    response = requests.get(f"{glpi_url}/ComputerModel/{model_id}", headers=headers, timeout=10)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()

def fetch_manufacturer_data(session_token, glpi_url, manufacturer_id):
    headers = {'Content-Type': 'application/json', 'Session-Token': session_token, 'App-Token': app_token}
    response = requests.get(f"{glpi_url}/Manufacturer/{manufacturer_id}", headers=headers, timeout=10)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()

def fetch_device_data(session_token, glpi_url, url):
    headers = {'Content-Type': 'application/json', 'Session-Token': session_token, 'App-Token': app_token}
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 404:
        return []
    response.raise_for_status()
    return response.json()

def fetch_designation_from_rel(session_token, glpi_url, device_data, rel_name):
    for link in device_data.get('links', []):
        if link['rel'] == rel_name:
            return fetch_designation(session_token, glpi_url, link['href'])
    return 'Unknown'

def fetch_designation(session_token, glpi_url, url):
    headers = {'Content-Type': 'application/json', 'Session-Token': session_token, 'App-Token': app_token}
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 404:
        return 'Unknown'
    response.raise_for_status()
    data = response.json()
    return data.get('designation', 'Unknown')

def fetch_designation_and_frequence(session_token, glpi_url, url):
    headers = {'Content-Type': 'application/json', 'Session-Token': session_token, 'App-Token': app_token}
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 404:
        return 'Unknown', None
    response.raise_for_status()
    data = response.json()
    designation = data.get('designation', 'Unknown')
    frequence = data.get('frequence', None)
    return designation, frequence
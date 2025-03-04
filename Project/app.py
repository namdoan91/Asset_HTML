import requests
import json
import time
import hashlib
from requests.exceptions import HTTPError
from flask import Flask, request, jsonify, render_template
import threading

app = Flask(__name__)

# Các thông số API GLPI và Snipe-IT
glpi_url = "http://10.0.2.99/apirest.php"
user_token = "jTTeNbes6AGS4RGsFkrnkr4AjvFUa1qL0uWwhk0D"
app_token = "JI8xe1yQM2hNYZsSoOmfxU1dzcnp0EC3IimduUNG"
snipe_it_url = "http://10.0.2.113/api/v1"
snipe_it_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiMGQzOTY1YzJkYTE2NjA1MGU1MDJkYmFkODgxMTk2MDkzMTkyMjM1ZTBiMjg2NjhkNGFjOGY1NDYxMzIxNzA2Y2IyZTY5ZjIwYzIzNjljZGUiLCJpYXQiOjE3MjE5NjAzNjguMTY1NTA3LCJuYmYiOjE3MjE5NjAzNjguMTY1NTA5LCJleHAiOjIxOTUyNTk1NjguMTYwMDIxLCJzdWIiOiI5OSIsinNjb3BlcyI6W119.sz-Sp4Bqh2KttHgzEKJFPvFeN68Jrcz_mvuBI43Sk23EzSMAi8308YWOuFVcp7bS5JznjMdEkgsrhlryQDLqi9wuHDDKy6DvlTJWZ03JA5Fk03DDmqYnO0UbsvEOeI7QlhAX40uS7O5_DEKPI4oY5OM4CrFljOB7wkEcwVkagaP5MDY8l73okx20mGyre4CWjiftNlXPYsBlgPsbd-oL9LEjgclMAz9i-V-TPVjau6GDNUKJa9UDTk1U2hA5J9XFxcrMZ67SrFdIdrEa3Kkdsg3o4M88D1SYb1QcG2P0k_BTE0MQra74EQ-suQvX4lpt0l0phEKD4-83Cd-MlE_e-PAIWqqtSkk1srYNrLBOw-LEvN7laf3y-2k2omFhomf8OwyxhxRlMnTxpjP8gRiDn_7saGh_3s_pTeQbwN7WoCfs9lTfQBKI-e8ZsDz3GYNyIY9h4QOvWfzkxJurfPbCyTDa1i3nIzH3Xt0SfqOXIVmLRt-sLqABeGbxiA7wr_gc6X568jqZ7AjlW_2xQbSPhes3WefVsJsbGPv6r8W4pPpIqemRuOFoHh93OowcTCPdcu-Qw1-UIMfr9r7NhZNFu-n47zJg6QGxqgh4cVMX-ySe3mBBb_bJCY7iASfjsPWUpApndO8QKaLzkwXOA11SqvTPidTzl46q4SfKDRPu26Q"

# Các category_id trên Snipe-IT cho components
categories = {
    'Item_DeviceHardDrive': 4,
    'Item_DeviceMemory': 5,
    'Item_DeviceGraphicCard': 6,
    'Item_DeviceProcessor': 13
}

category_mapping = {
    "Desktop/Workstation": 10,
    "Laptop/Notebook": 11,
    "Server": 12
}

logs = []

def log_message(message):
    timestamp = time.strftime('%H:%M:%S')
    logs.append(f"{timestamp} - {message}")
    print(f"{timestamp} - {message}")

# Các hàm từ NhapPC_New.py (giữ nguyên)
def determine_asset_category_id(category_name_or_id):
    if isinstance(category_name_or_id, str) and category_name_or_id in category_mapping:
        return category_mapping[category_name_or_id]
    type_mapping = {3: 11, 4: 11, 5: 12}
    return type_mapping.get(category_name_or_id, 10)

def format_asset_name(name):
    if not name:
        return name
    if '-' in name:
        return name
    if len(name) >= 2:
        return f"{name[:2]}-{name[2:]}"
    return name

def get_session_token():
    headers = {'Content-Type': 'application/json', 'Authorization': f'user_token {user_token}', 'App-Token': app_token}
    response = requests.get(f"{glpi_url}/initSession", headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()['session_token']

def fetch_computer_data(session_token, computer_id):
    headers = {'Content-Type': 'application/json', 'Session-Token': session_token, 'App-Token': app_token}
    response = requests.get(f"{glpi_url}/Computer/{computer_id}", headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()

def fetch_model_data(session_token, model_id):
    headers = {'Content-Type': 'application/json', 'Session-Token': session_token, 'App-Token': app_token}
    response = requests.get(f"{glpi_url}/ComputerModel/{model_id}", headers=headers, timeout=10)
    if response.status_code == 404:
        log_message(f"Model ID {model_id} not found in GLPI")
        return None
    response.raise_for_status()
    return response.json()

def fetch_manufacturer_data(session_token, manufacturer_id):
    headers = {'Content-Type': 'application/json', 'Session-Token': session_token, 'App-Token': app_token}
    response = requests.get(f"{glpi_url}/Manufacturer/{manufacturer_id}", headers=headers, timeout=10)
    if response.status_code == 404:
        log_message(f"Manufacturer ID {manufacturer_id} not found in GLPI")
        return None
    response.raise_for_status()
    return response.json()

def fetch_device_data(session_token, url):
    headers = {'Content-Type': 'application/json', 'Session-Token': session_token, 'App-Token': app_token}
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 404:
        log_message(f"URL not found: {url}")
        return []
    response.raise_for_status()
    return response.json()

def fetch_designation_from_rel(session_token, device_data, rel_name):
    for link in device_data.get('links', []):
        if link['rel'] == rel_name:
            return fetch_designation(session_token, link['href'])
    return 'Unknown'

def fetch_designation(session_token, url):
    headers = {'Content-Type': 'application/json', 'Session-Token': session_token, 'App-Token': app_token}
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 404:
        log_message(f"URL not found: {url}")
        return 'Unknown'
    response.raise_for_status()
    data = response.json()
    return data.get('designation', 'Unknown')

def fetch_designation_and_frequence(session_token, url):
    headers = {'Content-Type': 'application/json', 'Session-Token': session_token, 'App-Token': app_token}
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 404:
        log_message(f"URL not found: {url}")
        return 'Unknown', None
    response.raise_for_status()
    data = response.json()
    designation = data.get('designation', 'Unknown')
    frequence = data.get('frequence', None)
    return designation, frequence

def generate_unique_serial(device_name, memory_info, index=0):
    info_string = f"{device_name}_{memory_info.get('designation', 'Unknown')}_{memory_info.get('size', 'Unknown')}_{memory_info.get('frequence', 'Unknown')}_{index}"
    return hashlib.md5(info_string.encode()).hexdigest()[:10]

def get_asset_id(asset_name, sleep_time=2):
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {snipe_it_token}'}
    formatted_name = format_asset_name(asset_name)
    url = f"{snipe_it_url}/hardware?search={formatted_name}"
    time.sleep(sleep_time)
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    if data['total'] > 0:
        return data['rows'][0]['id']
    return None

def get_asset_details(asset_id, sleep_time=2):
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {snipe_it_token}'}
    url = f"{snipe_it_url}/hardware/{asset_id}"
    time.sleep(sleep_time)
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    return data

def check_manufacturer_in_snipe_it(manufacturer_name, sleep_time=2):
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {snipe_it_token}'}
    url = f"{snipe_it_url}/manufacturers?search={manufacturer_name}"
    time.sleep(sleep_time)
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    if data['total'] > 0:
        return data['rows'][0]['id']
    return None

def create_manufacturer_in_snipe_it(manufacturer_name, sleep_time=2):
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {snipe_it_token}'}
    payload = {"name": manufacturer_name}
    url = f"{snipe_it_url}/manufacturers"
    time.sleep(sleep_time)
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    if data.get('status') == 'success':
        return data['payload']['id']
    return None

def check_model_in_snipe_it(model_name, category_id, manufacturer_id, sleep_time=2):
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {snipe_it_token}'}
    url = f"{snipe_it_url}/models?search={model_name}"
    time.sleep(sleep_time)
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    if data['total'] > 0:
        return data['rows'][0]['id']
    return None

def create_model_in_snipe_it(model_name, category_id, manufacturer_id, sleep_time=2):
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {snipe_it_token}'}
    payload = {"name": model_name, "category_id": category_id, "manufacturer_id": manufacturer_id}
    url = f"{snipe_it_url}/models"
    time.sleep(sleep_time)
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    if data.get('status') == 'success':
        return data['payload']['id']
    return None

def create_asset_in_snipe_it(computer_info, model_id, category_id, sleep_time=2):
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {snipe_it_token}'}
    name = computer_info['name']
    formatted_name = format_asset_name(name)
    serial = computer_info.get('serial', '')
    status_id = computer_info.get('statuslabels_id', "4")
    payload = {
        "name": formatted_name,
        "asset_tag": formatted_name,
        "serial": serial,
        "category_id": category_id,
        "status_id": int(status_id),
        "model_id": model_id,
        "company_id": 1,
        "location_id": 1
    }
    url = f"{snipe_it_url}/hardware"
    time.sleep(sleep_time)
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    if data.get('status') == 'success':
        log_message(f"Created asset '{formatted_name}' in Snipe-IT with ID: {data['payload']['id']}")
        return data['payload']['id']
    return None

def fetch_categories_from_snipe_it():
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {snipe_it_token}'
    }
    url = f"{snipe_it_url}/categories"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        categories = [
            {'name': row['name'], 'id': row['id']}
            for row in data.get('rows', [])
            if row.get('components_count', 0) == 0
            and row.get('accessories_count', 0) == 0
            and row.get('consumables_count', 0) == 0
            and row.get('licenses_count', 0) == 0
        ]
        log_message(f"Các danh mục tài sản được tải từ ITAM: {len(categories)} items")
        return categories
    except Exception as e:
        log_message(f"Lỗi khi tải danh mục từ Snipe-IT: {str(e)}")
        return []

def fetch_status_labels_from_snipe_it():
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {snipe_it_token}'
    }
    url = f"{snipe_it_url}/statuslabels"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    status_labels = [{'name': row['name'], 'id': row['id']} for row in data.get('rows', [])]
    return status_labels

def fetch_user_by_employee_number(employee_number):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {snipe_it_token}'
    }
    url = f"{snipe_it_url}/users?search={employee_number}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    for user in data.get('rows', []):
        if user.get('employee_num') == employee_number:
            return {'name': user['name'], 'id': user['id'], 'employee_number': user.get('employee_num', '')}
    log_message(f"Không tìm thấy người dùng với mã số nhân viên: {employee_number}")
    return None

def prepare_component_data(computer_info, category_id):
    components = []
    name = computer_info['name'] if isinstance(computer_info['name'], str) else computer_info.get('name', '')
    if category_id == categories['Item_DeviceHardDrive']:
        for item in computer_info.get('itemharddisk', []):
            component = {
                'name': item.get('designation', 'Unknown Hard Drive'),
                'serial': item.get('serial', ''),
                'category_id': category_id,
                'model_number': item.get('id', '0'),
                'purchase_cost': 0,
                'status_id': 1,
                'company_id': 1,
                'location_id': 1,
                'qty': 1
            }
            components.append(component)
    elif category_id == categories['Item_DeviceMemory']:
        for item in computer_info.get('itemmemory', []):
            if not item.get("serial"):
                generated_serial = generate_unique_serial(name, item)
                item["serial"] = f"GEN-{generated_serial}"
                log_message(f"Generated unique serial {item['serial']} for device {name}")
            designation = item.get('designation', 'Unknown Memory')
            size = item.get('size', '0')
            frequence = item.get('frequence', '0')
            name = f"{designation} {size}MB {frequence}MHz" if size and frequence else designation
            component = {
                'name': name,
                'serial': item.get('serial', ''),
                'category_id': category_id,
                'model_number': item.get('id', '0'),
                'purchase_cost': 0,
                'status_id': 1,
                'company_id': 1,
                'location_id': 1,
                'qty': 1
            }
            components.append(component)
    elif category_id == categories['Item_DeviceGraphicCard']:
        graphic_cards = {}
        for item in computer_info.get('itemgraphic', []):
            name = item.get('designation', 'Unknown Graphic Card')
            if name in graphic_cards:
                graphic_cards[name]['qty'] += 1
            else:
                graphic_cards[name] = {
                    'name': name,
                    'serial': item.get('serial', ''),
                    'category_id': category_id,
                    'model_number': item.get('id', '0'),
                    'purchase_cost': 0,
                    'status_id': 1,
                    'company_id': 1,
                    'location_id': 1,
                    'qty': 1
                }
        components.extend(graphic_cards.values())
    elif category_id == categories['Item_DeviceProcessor']:
        processors = {}
        for item in computer_info.get('itemprocessor', []):
            name = item.get('designation', 'Unknown Processor')
            if name in processors:
                processors[name]['qty'] += 1
            else:
                processors[name] = {
                    'name': name,
                    'serial': item.get('serial', ''),
                    'category_id': category_id,
                    'model_number': item.get('id', '0'),
                    'purchase_cost': 0,
                    'status_id': 1,
                    'company_id': 1,
                    'location_id': 1,
                    'qty': 1
                }
        components.extend(processors.values())
    return components

def import_component_to_snipe_it(component, max_retries=3, sleep_time=0.5):
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {snipe_it_token}'}
    for attempt in range(max_retries):
        try:
            time.sleep(sleep_time)
            if component['category_id'] in [categories['Item_DeviceHardDrive'], categories['Item_DeviceMemory']]:
                url = f"{snipe_it_url}/components"
                response = requests.post(url, headers=headers, json=component)
            else:
                existing_component = get_existing_component(component['name'], component['category_id'])
                if existing_component:
                    url = f"{snipe_it_url}/components/{existing_component['id']}"
                    component['qty'] += existing_component['qty']
                    response = requests.put(url, headers=headers, json=component)
                else:
                    url = f"{snipe_it_url}/components"
                    response = requests.post(url, headers=headers, json=component)
            response.raise_for_status()
            response_data = response.json()
            if response_data.get('status') == 'success':
                return response_data['payload']['id']
        except Exception as e:
            log_message(f"Error importing component: {e}")
    return None

def get_existing_component(name, category_id):
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {snipe_it_token}'}
    url = f"{snipe_it_url}/components?search={name}&category_id={category_id}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    if data['total'] > 0:
        return data['rows'][0]
    return None

def link_component_to_asset(component_id, asset_id, sleep_time=2):
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {snipe_it_token}'}
    payload = {"assigned_to": asset_id, "checkout_to_type": "asset", "assigned_qty": 1}
    url = f"{snipe_it_url}/components/{component_id}/checkout"
    time.sleep(sleep_time)
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    log_message(f"Successfully linked component {component_id} to asset {asset_id}")

def format_display(computer_info, components_dict, category_name, model_name, manufacturer_name, snipe_info):
    display_text = "=== Thông tin thiết bị ===\n"
    is_manual = not any(isinstance(v, (list, dict)) for v in computer_info.values() if v not in ['name', 'serial'])  # Kiểm tra đơn giản
    
    if is_manual:
        name = computer_info['name']
        formatted_name = format_asset_name(name)
        serial = computer_info.get('serial', 'Không có')
        display_text += f"GLPI{'':<30} | Snipe-IT{'':<30}\n"
        display_text += "-" * 80 + "\n"
        display_text += f"Asset Name: {formatted_name:<30} | {snipe_info['name'] if snipe_info and 'name' in snipe_info else 'Không có':<30}\n"
        display_text += f"Asset Tag: {formatted_name:<30} | {snipe_info['asset_tag'] if snipe_info and 'asset_tag' in snipe_info else 'Không có':<30}\n"
        display_text += f"Serial: {serial:<30} | {snipe_info['serial'] if snipe_info and 'serial' in snipe_info else 'Không có':<30}\n"
        display_text += f"Category: {category_name:<30} | {snipe_info['category']['name'] if snipe_info and 'category' in snipe_info and 'name' in snipe_info['category'] else 'Không có':<30}\n"
        display_text += f"Model: {model_name:<30} | {snipe_info['model']['name'] if snipe_info and 'model' in snipe_info and 'name' in snipe_info['model'] else 'Không có':<30}\n"
        display_text += f"Manufacturer: {manufacturer_name:<30} | {snipe_info['manufacturer']['name'] if snipe_info and 'manufacturer' in snipe_info and 'name' in snipe_info['manufacturer'] else 'Không có':<30}\n"
    else:
        name = computer_info['name']
        formatted_name = format_asset_name(name)
        serial = computer_info.get('serial', 'Không có')
        display_text += f"GLPI{'':<40}\n"
        display_text += "-" * 40 + "\n"
        display_text += f"Asset Name: {formatted_name}\n"
        display_text += f"Asset Tag: {formatted_name}\n"
        display_text += f"Serial: {serial}\n"
        display_text += f"Category: {category_name}\n"
        display_text += f"Model: {model_name}\n"
        display_text += f"Manufacturer: {manufacturer_name}\n"
        status_id = computer_info.get('statuslabels_id', '4')
        display_text += f"Status ID: {status_id}\n"
        employee_number = computer_info.get('employee_number', '')
        assigned_to_name = "Không có"
        if employee_number:
            user = fetch_user_by_employee_number(employee_number)
            if user:
                assigned_to_name = user['name']
        display_text += f"Checkout đến: {assigned_to_name} (MSNV: {employee_number or 'Không có'})\n"

    # Hiển thị components
    for category_name in components_dict.keys():
        display_text += f"\n=== {category_name} ===\n"
        display_text += f"{'GLPI':<40}\n"
        display_text += "-" * 40 + "\n"
        glpi_components = components_dict.get(category_name, [])
        for i, glpi_comp in enumerate(glpi_components, 1):
            glpi_line = f"{i}. {glpi_comp.get('name', 'Unknown')} ({glpi_comp.get('serial', 'Không có')}, Qty: {glpi_comp.get('qty', 1)})"
            display_text += f"{glpi_line:<40}\n"

    return display_text

# Routes
@app.route('/')
def home():
    return render_template('index.html', logs=logs)

@app.route('/fetch_glpi', methods=['POST'])
def fetch_glpi():
    data = request.get_json()
    computer_id = data.get('computer_id', '')
    if not computer_id:
        return jsonify({'error': 'Vui lòng nhập ID máy tính!'}), 400
    
    log_message(f"Bắt đầu xử lý computer ID: {computer_id}")
    try:
        session_token = get_session_token()
        computer_data = fetch_computer_data(session_token, computer_id)
        computer_info = {
            'name': computer_data['name'],
            'serial': computer_data.get('serial', ''),
            'computertypes_id': computer_data.get('computertypes_id', 0),
            'computermodels_id': computer_data.get('computermodels_id', 0),
            'manufacturers_id': computer_data.get('manufacturers_id', 0),
            'itemprocessor': [],
            'itemmemory': [],
            'itemharddisk': [],
            'itemgraphic': []
        }

        model_name = "Unknown"
        if computer_info['computermodels_id'] != 0:
            model_data = fetch_model_data(session_token, computer_info['computermodels_id'])
            if model_data:
                model_name = model_data.get('name', 'Unknown')

        manufacturer_name = "Unknown"
        if computer_info['manufacturers_id'] != 0:
            manufacturer_data = fetch_manufacturer_data(session_token, computer_info['manufacturers_id'])
            if manufacturer_data:
                manufacturer_name = manufacturer_data.get('name', 'Unknown')

        for link in computer_data.get('links', []):
            rel = link['rel']
            href = link['href']
            if rel == 'Item_DeviceProcessor':
                processors = fetch_device_data(session_token, href)
                for processor in processors:
                    designation = fetch_designation_from_rel(session_token, processor, 'DeviceProcessor')
                    computer_info['itemprocessor'].append({
                        'id': processor['id'],
                        'frequency': processor.get('frequency'),
                        'designation': designation
                    })
            elif rel == 'Item_DeviceMemory':
                memories = fetch_device_data(session_token, href)
                for index, memory in enumerate(memories):
                    designation, frequence = fetch_designation_and_frequence(session_token, f"{glpi_url}/DeviceMemory/{memory['devicememories_id']}")
                    if not memory.get("serial"):
                        generated_serial = generate_unique_serial(computer_info['name'], memory, index)
                        memory["serial"] = f"GEN-{generated_serial}"
                    computer_info['itemmemory'].append({
                        'id': memory['id'],
                        'size': memory.get('size'),
                        'serial': memory['serial'],
                        'frequence': frequence,
                        'designation': designation
                    })
            elif rel == 'Item_DeviceHardDrive':
                harddrives = fetch_device_data(session_token, href)
                for harddrive in harddrives:
                    designation = fetch_designation_from_rel(session_token, harddrive, 'DeviceHardDrive')
                    computer_info['itemharddisk'].append({
                        'id': harddrive['id'],
                        'capacity': harddrive.get('capacity'),
                        'serial': harddrive.get('serial', ''),
                        'designation': designation
                    })
            elif rel == 'Item_DeviceGraphicCard':
                graphics = fetch_device_data(session_token, href)
                for graphic in graphics:
                    designation = fetch_designation_from_rel(session_token, graphic, 'DeviceGraphicCard')
                    computer_info['itemgraphic'].append({
                        'id': graphic['id'],
                        'memory': graphic.get('memory'),
                        'serial': graphic.get('serial', ''),
                        'designation': designation
                    })
        
        log_message(f"Processed computer {computer_id} from GLPI")
        asset_category_id = determine_asset_category_id(computer_info['computertypes_id'])
        category_names = {10: "Desktop/Workstation", 11: "Laptop/Notebook", 12: "Server"}
        category_name = category_names.get(asset_category_id, "Desktop/Workstation")
        components_dict = {}
        for category_name_key, category_id in categories.items():
            components_dict[category_name_key] = prepare_component_data(computer_info, category_id)
        asset_id = get_asset_id(computer_info['name'])
        snipe_info = None
        if asset_id:
            snipe_info = get_asset_details(asset_id)
            log_message(f"Found asset {format_asset_name(computer_info['name'])} in Snipe-IT with ID: {asset_id}")
        else:
            log_message(f"Asset {format_asset_name(computer_info['name'])} not found in Snipe-IT")

        display_text = format_display(computer_info, components_dict, category_name, model_name, manufacturer_name, snipe_info)
        return jsonify({'display_text': display_text, 'logs': logs[-10:]})
    except Exception as e:
        log_message(f"Lỗi: {str(e)}")
        return jsonify({'error': str(e), 'logs': logs[-10:]}), 500

@app.route('/import_snipe_it', methods=['POST'])
def import_snipe_it_route():
    data = request.get_json()
    computer_id = data.get('computer_id', '')
    if not computer_id:
        return jsonify({'error': 'Vui lòng nhập ID máy tính!'}), 400
    
    def run_import():
        try:
            session_token = get_session_token()
            computer_data = fetch_computer_data(session_token, computer_id)
            computer_info = {
                'name': computer_data['name'],
                'serial': computer_data.get('serial', ''),
                'computertypes_id': computer_data.get('computertypes_id', 0),
                'computermodels_id': computer_data.get('computermodels_id', 0),
                'manufacturers_id': computer_data.get('manufacturers_id', 0),
                'itemprocessor': [],
                'itemmemory': [],
                'itemharddisk': [],
                'itemgraphic': []
            }
            model_name = "Unknown"
            if computer_info['computermodels_id'] != 0:
                model_data = fetch_model_data(session_token, computer_info['computermodels_id'])
                if model_data:
                    model_name = model_data.get('name', 'Unknown')

            manufacturer_name = "Unknown"
            if computer_info['manufacturers_id'] != 0:
                manufacturer_data = fetch_manufacturer_data(session_token, computer_info['manufacturers_id'])
                if manufacturer_data:
                    manufacturer_name = manufacturer_data.get('name', 'Unknown')

            for link in computer_data.get('links', []):
                rel = link['rel']
                href = link['href']
                if rel == 'Item_DeviceProcessor':
                    processors = fetch_device_data(session_token, href)
                    for processor in processors:
                        designation = fetch_designation_from_rel(session_token, processor, 'DeviceProcessor')
                        computer_info['itemprocessor'].append({
                            'id': processor['id'],
                            'frequency': processor.get('frequency'),
                            'designation': designation
                        })
                elif rel == 'Item_DeviceMemory':
                    memories = fetch_device_data(session_token, href)
                    for index, memory in enumerate(memories):
                        designation, frequence = fetch_designation_and_frequence(session_token, f"{glpi_url}/DeviceMemory/{memory['devicememories_id']}")
                        if not memory.get("serial"):
                            generated_serial = generate_unique_serial(computer_info['name'], memory, index)
                            memory["serial"] = f"GEN-{generated_serial}"
                        computer_info['itemmemory'].append({
                            'id': memory['id'],
                            'size': memory.get('size'),
                            'serial': memory['serial'],
                            'frequence': frequence,
                            'designation': designation
                        })
                elif rel == 'Item_DeviceHardDrive':
                    harddrives = fetch_device_data(session_token, href)
                    for harddrive in harddrives:
                        designation = fetch_designation_from_rel(session_token, harddrive, 'DeviceHardDrive')
                        computer_info['itemharddisk'].append({
                            'id': harddrive['id'],
                            'capacity': harddrive.get('capacity'),
                            'serial': harddrive.get('serial', ''),
                            'designation': designation
                        })
                elif rel == 'Item_DeviceGraphicCard':
                    graphics = fetch_device_data(session_token, href)
                    for graphic in graphics:
                        designation = fetch_designation_from_rel(session_token, graphic, 'DeviceGraphicCard')
                        computer_info['itemgraphic'].append({
                            'id': graphic['id'],
                            'memory': graphic.get('memory'),
                            'serial': graphic.get('serial', ''),
                            'designation': designation
                        })
            
            asset_category_id = determine_asset_category_id(computer_info['computertypes_id'])
            manufacturer_id = check_manufacturer_in_snipe_it(manufacturer_name) or create_manufacturer_in_snipe_it(manufacturer_name) or 1
            model_id = check_model_in_snipe_it(model_name, asset_category_id, manufacturer_id) or create_model_in_snipe_it(model_name, asset_category_id, manufacturer_id) or 1
            asset_id = get_asset_id(computer_info['name']) or create_asset_in_snipe_it(computer_info, model_id, asset_category_id)
            log_message("Completed importing data from GLPI to Snipe-IT")
        except Exception as e:
            log_message(f"Lỗi: {str(e)}")

    threading.Thread(target=run_import).start()
    return jsonify({'message': 'Đang xử lý import...', 'logs': logs[-10:]})

@app.route('/display_manual', methods=['POST'])
def display_manual():
    data = request.get_json()
    manual_info = {
        'name': data.get('name', ''),
        'serial': data.get('serial', ''),
        'computertypes_id': data.get('computertypes_id', ''),
        'model': data.get('model', ''),
        'manufacturer': data.get('manufacturer', ''),
        'statuslabels_id': data.get('statuslabels_id', '4'),
        'employee_number': data.get('employee_number', ''),
        'itemharddisk': data.get('itemharddisk', []),
        'itemmemory': data.get('itemmemory', []),
        'itemgraphic': data.get('itemgraphic', []),
        'itemprocessor': data.get('itemprocessor', [])
    }
    
    employee_number = manual_info['employee_number']
    assigned_to_name = "Không có"
    if employee_number:
        user = fetch_user_by_employee_number(employee_number)
        if user:
            assigned_to_name = user['name']
            log_message(f"Tìm thấy người dùng: {assigned_to_name} (MSNV: {employee_number})")
    
    components_dict = {}
    for category_name_key, category_id in categories.items():
        components_dict[category_name_key] = prepare_component_data(manual_info, category_id)
    
    display_text = "=== Thông tin thiết bị ===\n"
    name = manual_info['name']
    formatted_name = format_asset_name(name)
    serial = manual_info['serial'] or "Không có"
    category = manual_info['computertypes_id']
    model = manual_info['model']
    manufacturer = manual_info['manufacturer']
    status = manual_info['statuslabels_id']

    display_text += f"GLPI{'':<40}\n"
    display_text += "-" * 40 + "\n"
    display_text += f"Asset Name: {formatted_name}\n"
    display_text += f"Asset Tag: {formatted_name}\n"
    display_text += f"Serial: {serial}\n"
    display_text += f"Category: {category}\n"
    display_text += f"Model: {model}\n"
    display_text += f"Manufacturer: {manufacturer}\n"
    display_text += f"Status ID: {status}\n"
    display_text += f"Checkout đến: {assigned_to_name} (MSNV: {employee_number or 'Không có'})\n"

    # Hiển thị components
    for category_name in components_dict.keys():
        display_text += f"\n=== {category_name} ===\n"
        display_text += f"{'GLPI':<40}\n"
        display_text += "-" * 40 + "\n"
        glpi_components = components_dict.get(category_name, [])
        for i, glpi_comp in enumerate(glpi_components, 1):
            glpi_line = f"{i}. {glpi_comp.get('name', 'Unknown')} ({glpi_comp.get('serial', 'Không có')}, Qty: {glpi_comp.get('qty', 1)})"
            display_text += f"{glpi_line:<40}\n"

    return jsonify({'info': display_text, 'logs': logs[-10:]})

@app.route('/import_manual', methods=['POST'])
def import_manual():
    data = request.get_json()
    computer_info = {
        'name': data.get('name', ''),
        'serial': data.get('serial', ''),
        'computertypes_id': data.get('computertypes_id', ''),
        'model': data.get('model', ''),
        'manufacturer': data.get('manufacturer', ''),
        'statuslabels_id': data.get('statuslabels_id', '4'),
        'employee_number': data.get('employee_number', ''),
        'itemharddisk': data.get('itemharddisk', []),
        'itemmemory': data.get('itemmemory', []),
        'itemgraphic': data.get('itemgraphic', []),
        'itemprocessor': data.get('itemprocessor', [])
    }
    
    def run_import():
        try:
            log_message(f"Bắt đầu import thủ công cho asset: {computer_info['name']}")
            model_name = computer_info['model'] or "Unknown"
            manufacturer_name = computer_info['manufacturer'] or "Unknown"
            asset_category_id = determine_asset_category_id(computer_info['computertypes_id'])
            manufacturer_id = check_manufacturer_in_snipe_it(manufacturer_name) or create_manufacturer_in_snipe_it(manufacturer_name) or 1
            model_id = check_model_in_snipe_it(model_name, asset_category_id, manufacturer_id) or create_model_in_snipe_it(model_name, asset_category_id, manufacturer_id) or 1
            asset_id = get_asset_id(computer_info['name']) or create_asset_in_snipe_it(computer_info, model_id, asset_category_id)
            
            employee_number = computer_info['employee_number']
            if employee_number:
                user = fetch_user_by_employee_number(employee_number)
                if user:
                    headers = {
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {snipe_it_token}'
                    }
                    payload = {"assigned_to": user['id'], "checkout_to_type": "user"}
                    url = f"{snipe_it_url}/hardware/{asset_id}/checkout"
                    response = requests.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                    log_message(f"Checked out asset {asset_id} to {user['name']} (MSNV: {employee_number})")
            
            components_dict = {}
            for category_name_key, category_id in categories.items():
                components_dict[category_name_key] = prepare_component_data(computer_info, category_id)
            
            for category_name, components in components_dict.items():
                for component in components:
                    component_id = import_component_to_snipe_it(component)
                    if component_id:
                        link_component_to_asset(component_id, asset_id)

            log_message("Completed importing manual data and linking components")
        except Exception as e:
            log_message(f"Lỗi: {str(e)}")

    threading.Thread(target=run_import).start()
    return jsonify({'message': 'Đang xử lý import...', 'logs': logs[-10:]})

@app.route('/search_asset', methods=['POST'])
def search_asset():
    data = request.get_json()
    serial_number = data.get('serial_number', '')
    if not serial_number:
        return jsonify({'error': 'Vui lòng nhập số serial hoặc quét QR Code!'}), 400
    
    prefix_to_remove = "http://10.0.2.113/ht/"
    if serial_number.startswith(prefix_to_remove):
        asset_tag = serial_number[len(prefix_to_remove):].strip()
        log_message(f"Đã quét QR Code: {serial_number}. Tìm kiếm tài sản với asset_tag: {asset_tag}")
    else:
        asset_tag = serial_number
        log_message(f"Bắt đầu tìm kiếm tài sản với serial/asset_tag: {asset_tag}")
    
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {snipe_it_token}'}
    url = f"{snipe_it_url}/hardware?search={asset_tag}&search_field=serial"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    assets = data.get('rows', [])
    
    display_text = ""
    for asset in assets:
        display_text += "=== Thông tin tài sản ===\n"
        display_text += f"ID: {asset.get('id', 'Không có')}\n"
        display_text += f"Tên tài sản: {asset.get('name', 'Không có')}\n"
        display_text += f"Thẻ tài sản: {asset.get('asset_tag', 'Không có')}\n"
        display_text += f"Serial: {asset.get('serial', 'Không có')}\n"
        model_name = asset.get('model', {}).get('name', 'Không có')
        display_text += f"Kiểu thiết bị: {model_name}\n"
        status_label = asset.get('status_label', {}).get('name', 'Không có')
        display_text += f"Trạng Thái thiết bị: {status_label}\n"
        category_name = asset.get('category', {}).get('name', 'Không có')
        display_text += f"Kiểu tài sản: {category_name}\n"
        manufacturer = asset.get('manufacturer')
        manufacturer_name = asset.get('manufacturer', {}).get('name', 'Không có') if manufacturer is not None else 'Không có'
        display_text += f"Nhà Sản Xuất: {manufacturer_name}\n"
        company_name = asset.get('company', {}).get('name', 'Không có')
        display_text += f"Công Ty: {company_name}\n"
        assigned_to = asset.get('assigned_to', {})
        if assigned_to and assigned_to.get('type') == 'asset':
            assigned_to_name = assigned_to.get('name', 'Không có')
            display_text += f"Tài sản liên kết: {assigned_to_name}\n"
        else:
            assigned_to_name = assigned_to.get('name', 'Không có') if assigned_to else 'Không có'
            display_text += f"Được cấp cho: {assigned_to_name}\n"
            assigned_to_email = assigned_to.get('email', 'Không có') if assigned_to else 'Không có'
            display_text += f"Email: {assigned_to_email}\n"
            assigned_to_employee_number = assigned_to.get('employee_number', 'Không có') if assigned_to else 'Không có'
            display_text += f"MSNV được cấp: {assigned_to_employee_number}\n"
        checkout_date = asset.get('last_checkout', {}).get('datetime', 'Không có') if asset.get('last_checkout') else 'Không có'
        display_text += f"Ngày được cấp: {checkout_date}\n"
        created_by = asset.get('created_by', {}).get('name', 'Không có') if asset.get('created_by') else 'Không có'
        display_text += f"Người tạo bởi: {created_by}\n"
        display_text += "-" * 40 + "\n"

    return jsonify({'display_text': display_text, 'logs': logs[-10:]})

@app.route('/get_categories', methods=['GET'])
def get_categories():
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {snipe_it_token}'
    }
    url = f"{snipe_it_url}/categories"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        categories = [
            {'name': row['name'], 'id': row['id']}
            for row in data.get('rows', [])
            if row.get('components_count', 0) == 0
            and row.get('accessories_count', 0) == 0
            and row.get('consumables_count', 0) == 0
            and row.get('licenses_count', 0) == 0
        ]
        log_message(f"Các danh mục tài sản được tải từ ITAM: {len(categories)} items")
        return jsonify({'categories': [cat['name'] for cat in categories]})
    except requests.RequestException as e:
        log_message(f"Lỗi khi tải danh mục từ Snipe-IT: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_status_labels', methods=['GET'])
def get_status_labels():
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {snipe_it_token}'
    }
    url = f"{snipe_it_url}/statuslabels"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    status_labels = [{'name': row['name'], 'id': row['id']} for row in data.get('rows', [])]
    return jsonify({'status_labels': [f"{status['name']} (ID: {status['id']})" for status in status_labels]})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
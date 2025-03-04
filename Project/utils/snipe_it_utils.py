import requests
import time
import hashlib

def format_asset_name(name):
    if not name:
        return name
    if '-' in name:
        return name
    if len(name) >= 2:
        return f"{name[:2]}-{name[2:]}"
    return name

def generate_unique_serial(device_name, memory_info, index=0):
    info_string = f"{device_name}_{memory_info.get('designation', 'Unknown')}_{memory_info.get('size', 'Unknown')}_{memory_info.get('frequence', 'Unknown')}_{index}"
    return hashlib.md5(info_string.encode()).hexdigest()[:10]

def get_asset_id(snipe_it_url, snipe_it_token, asset_name, sleep_time=2):
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

def get_asset_details(snipe_it_url, snipe_it_token, asset_id, sleep_time=2):
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {snipe_it_token}'}
    url = f"{snipe_it_url}/hardware/{asset_id}"
    time.sleep(sleep_time)
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    return data

def check_manufacturer_in_snipe_it(snipe_it_url, snipe_it_token, manufacturer_name, sleep_time=2):
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {snipe_it_token}'}
    url = f"{snipe_it_url}/manufacturers?search={manufacturer_name}"
    time.sleep(sleep_time)
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    if data['total'] > 0:
        return data['rows'][0]['id']
    return None

def create_manufacturer_in_snipe_it(snipe_it_url, snipe_it_token, manufacturer_name, sleep_time=2):
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

def check_model_in_snipe_it(snipe_it_url, snipe_it_token, model_name, category_id, manufacturer_id, sleep_time=2):
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {snipe_it_token}'}
    url = f"{snipe_it_url}/models?search={model_name}"
    time.sleep(sleep_time)
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    if data['total'] > 0:
        return data['rows'][0]['id']
    return None

def create_model_in_snipe_it(snipe_it_url, snipe_it_token, model_name, category_id, manufacturer_id, sleep_time=2):
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

def create_asset_in_snipe_it(snipe_it_url, snipe_it_token, computer_info, model_id, category_id, sleep_time=2):
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
        return data['payload']['id']
    return None

def fetch_categories_from_snipe_it(snipe_it_url, snipe_it_token):
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
        return categories
    except requests.RequestException as e:
        return []

def fetch_status_labels_from_snipe_it(snipe_it_url, snipe_it_token):
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

def fetch_user_by_employee_number(snipe_it_url, snipe_it_token, employee_number):
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
    return None

def prepare_component_data(computer_info, category_id, categories):
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

def import_component_to_snipe_it(snipe_it_url, snipe_it_token, component, max_retries=3, sleep_time=0.5):
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {snipe_it_token}'}
    for attempt in range(max_retries):
        try:
            time.sleep(sleep_time)
            if component['category_id'] in [categories['Item_DeviceHardDrive'], categories['Item_DeviceMemory']]:
                url = f"{snipe_it_url}/components"
                response = requests.post(url, headers=headers, json=component)
            else:
                existing_component = get_existing_component(snipe_it_url, snipe_it_token, component['name'], component['category_id'])
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
            print(f"Error importing component: {e}")
    return None

def get_existing_component(snipe_it_url, snipe_it_token, name, category_id):
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {snipe_it_token}'}
    url = f"{snipe_it_url}/components?search={name}&category_id={category_id}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    if data['total'] > 0:
        return data['rows'][0]
    return None

def link_component_to_asset(snipe_it_url, snipe_it_token, component_id, asset_id, sleep_time=2):
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {snipe_it_token}'}
    payload = {"assigned_to": asset_id, "checkout_to_type": "asset", "assigned_qty": 1}
    url = f"{snipe_it_url}/components/{component_id}/checkout"
    time.sleep(sleep_time)
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

def determine_asset_category_id(category_name_or_id, category_mapping):
    if isinstance(category_name_or_id, str) and category_name_or_id in category_mapping:
        return category_mapping[category_name_or_id]
    type_mapping = {3: 11, 4: 11, 5: 12}
    return type_mapping.get(category_name_or_id, 10)

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
            user = fetch_user_by_employee_number(snipe_it_url, snipe_it_token, employee_number)
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
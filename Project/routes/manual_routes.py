from flask import Blueprint, request, jsonify
import config
from utils.glpi_utils import *
from utils.snipe_it_utils import *
from utils.logging_utils import *

bp = Blueprint('manual', __name__)

@bp.route('/display_manual', methods=['POST'])
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
        user = fetch_user_by_employee_number(config.snipe_it_url, config.snipe_it_token, employee_number)
        if user:
            assigned_to_name = user['name']
            log_message(f"Tìm thấy người dùng: {assigned_to_name} (MSNV: {employee_number})")
    
    components_dict = {}
    for category_name_key, category_id in config.categories.items():
        components_dict[category_name_key] = prepare_component_data(manual_info, category_id, config.categories)
    
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

@bp.route('/import_manual', methods=['POST'])
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
            asset_category_id = determine_asset_category_id(computer_info['computertypes_id'], config.category_mapping)
            manufacturer_id = check_manufacturer_in_snipe_it(config.snipe_it_url, config.snipe_it_token, manufacturer_name) or create_manufacturer_in_snipe_it(config.snipe_it_url, config.snipe_it_token, manufacturer_name) or 1
            model_id = check_model_in_snipe_it(config.snipe_it_url, config.snipe_it_token, model_name, asset_category_id, manufacturer_id) or create_model_in_snipe_it(config.snipe_it_url, config.snipe_it_token, model_name, asset_category_id, manufacturer_id) or 1
            asset_id = get_asset_id(config.snipe_it_url, config.snipe_it_token, computer_info['name']) or create_asset_in_snipe_it(config.snipe_it_url, config.snipe_it_token, computer_info, model_id, asset_category_id)
            
            employee_number = computer_info['employee_number']
            if employee_number:
                user = fetch_user_by_employee_number(config.snipe_it_url, config.snipe_it_token, employee_number)
                if user:
                    headers = {
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {config.snipe_it_token}'
                    }
                    payload = {"assigned_to": user['id'], "checkout_to_type": "user"}
                    url = f"{config.snipe_it_url}/hardware/{asset_id}/checkout"
                    response = requests.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                    log_message(f"Checked out asset {asset_id} to {user['name']} (MSNV: {employee_number})")
            
            components_dict = {}
            for category_name_key, category_id in config.categories.items():
                components_dict[category_name_key] = prepare_component_data(computer_info, category_id, config.categories)
            
            for category_name, components in components_dict.items():
                for component in components:
                    component_id = import_component_to_snipe_it(config.snipe_it_url, config.snipe_it_token, component)
                    if component_id:
                        link_component_to_asset(config.snipe_it_url, config.snipe_it_token, component_id, asset_id)

            log_message("Completed importing manual data and linking components")
        except Exception as e:
            log_message(f"Lỗi: {str(e)}")

    threading.Thread(target=run_import).start()
    return jsonify({'message': 'Đang xử lý import...', 'logs': logs[-10:]})

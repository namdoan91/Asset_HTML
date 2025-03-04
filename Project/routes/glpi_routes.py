from flask import Blueprint, request, jsonify
import config
from utils.glpi_utils import *
from utils.snipe_it_utils import *
from utils.logging_utils import *

bp = Blueprint('glpi', __name__)

@bp.route('/fetch_glpi', methods=['POST'])
def fetch_glpi():
    data = request.get_json()
    computer_id = data.get('computer_id', '')
    if not computer_id:
        return jsonify({'error': 'Vui lòng nhập ID máy tính!'}), 400
    
    log_message(f"Bắt đầu xử lý computer ID: {computer_id}")
    try:
        session_token = get_session_token(config.glpi_url, config.user_token, config.app_token)
        computer_data = fetch_computer_data(session_token, config.glpi_url, computer_id)
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
            model_data = fetch_model_data(session_token, config.glpi_url, computer_info['computermodels_id'])
            if model_data:
                model_name = model_data.get('name', 'Unknown')

        manufacturer_name = "Unknown"
        if computer_info['manufacturers_id'] != 0:
            manufacturer_data = fetch_manufacturer_data(session_token, config.glpi_url, computer_info['manufacturers_id'])
            if manufacturer_data:
                manufacturer_name = manufacturer_data.get('name', 'Unknown')

        for link in computer_data.get('links', []):
            rel = link['rel']
            href = link['href']
            if rel == 'Item_DeviceProcessor':
                processors = fetch_device_data(session_token, config.glpi_url, href)
                for processor in processors:
                    designation = fetch_designation_from_rel(session_token, config.glpi_url, processor, 'DeviceProcessor')
                    computer_info['itemprocessor'].append({
                        'id': processor['id'],
                        'frequency': processor.get('frequency'),
                        'designation': designation
                    })
            elif rel == 'Item_DeviceMemory':
                memories = fetch_device_data(session_token, config.glpi_url, href)
                for index, memory in enumerate(memories):
                    designation, frequence = fetch_designation_and_frequence(session_token, config.glpi_url, f"{config.glpi_url}/DeviceMemory/{memory['devicememories_id']}")
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
                harddrives = fetch_device_data(session_token, config.glpi_url, href)
                for harddrive in harddrives:
                    designation = fetch_designation_from_rel(session_token, config.glpi_url, harddrive, 'DeviceHardDrive')
                    computer_info['itemharddisk'].append({
                        'id': harddrive['id'],
                        'capacity': harddrive.get('capacity'),
                        'serial': harddrive.get('serial', ''),
                        'designation': designation
                    })
            elif rel == 'Item_DeviceGraphicCard':
                graphics = fetch_device_data(session_token, config.glpi_url, href)
                for graphic in graphics:
                    designation = fetch_designation_from_rel(session_token, config.glpi_url, graphic, 'DeviceGraphicCard')
                    computer_info['itemgraphic'].append({
                        'id': graphic['id'],
                        'memory': graphic.get('memory'),
                        'serial': graphic.get('serial', ''),
                        'designation': designation
                    })
        
        log_message(f"Processed computer {computer_id} from GLPI")
        asset_category_id = determine_asset_category_id(computer_info['computertypes_id'], config.category_mapping)
        category_names = {10: "Desktop/Workstation", 11: "Laptop/Notebook", 12: "Server"}
        category_name = category_names.get(asset_category_id, "Desktop/Workstation")
        components_dict = {}
        for category_name_key, category_id in config.categories.items():
            components_dict[category_name_key] = prepare_component_data(computer_info, category_id, config.categories)
        asset_id = get_asset_id(config.snipe_it_url, config.snipe_it_token, computer_info['name'])
        snipe_info = None
        if asset_id:
            snipe_info = get_asset_details(config.snipe_it_url, config.snipe_it_token, asset_id)
            log_message(f"Found asset {format_asset_name(computer_info['name'])} in Snipe-IT with ID: {asset_id}")
        else:
            log_message(f"Asset {format_asset_name(computer_info['name'])} not found in Snipe-IT")

        display_text = format_display(computer_info, components_dict, category_name, model_name, manufacturer_name, snipe_info)
        return jsonify({'display_text': display_text, 'logs': logs[-10:]})
    except Exception as e:
        log_message(f"Lỗi: {str(e)}")
        return jsonify({'error': str(e), 'logs': logs[-10:]}), 500

@bp.route('/import_snipe_it', methods=['POST'])
def import_snipe_it_route():
    data = request.get_json()
    computer_id = data.get('computer_id', '')
    if not computer_id:
        return jsonify({'error': 'Vui lòng nhập ID máy tính!'}), 400
    
    def run_import():
        try:
            session_token = get_session_token(config.glpi_url, config.user_token, config.app_token)
            computer_data = fetch_computer_data(session_token, config.glpi_url, computer_id)
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
                model_data = fetch_model_data(session_token, config.glpi_url, computer_info['computermodels_id'])
                if model_data:
                    model_name = model_data.get('name', 'Unknown')

            manufacturer_name = "Unknown"
            if computer_info['manufacturers_id'] != 0:
                manufacturer_data = fetch_manufacturer_data(session_token, config.glpi_url, computer_info['manufacturers_id'])
                if manufacturer_data:
                    manufacturer_name = manufacturer_data.get('name', 'Unknown')

            for link in computer_data.get('links', []):
                rel = link['rel']
                href = link['href']
                if rel == 'Item_DeviceProcessor':
                    processors = fetch_device_data(session_token, config.glpi_url, href)
                    for processor in processors:
                        designation = fetch_designation_from_rel(session_token, config.glpi_url, processor, 'DeviceProcessor')
                        computer_info['itemprocessor'].append({
                            'id': processor['id'],
                            'frequency': processor.get('frequency'),
                            'designation': designation
                        })
                elif rel == 'Item_DeviceMemory':
                    memories = fetch_device_data(session_token, config.glpi_url, href)
                    for index, memory in enumerate(memories):
                        designation, frequence = fetch_designation_and_frequence(session_token, config.glpi_url, f"{config.glpi_url}/DeviceMemory/{memory['devicememories_id']}")
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
                    harddrives = fetch_device_data(session_token, config.glpi_url, href)
                    for harddrive in harddrives:
                        designation = fetch_designation_from_rel(session_token, config.glpi_url, harddrive, 'DeviceHardDrive')
                        computer_info['itemharddisk'].append({
                            'id': harddrive['id'],
                            'capacity': harddrive.get('capacity'),
                            'serial': harddrive.get('serial', ''),
                            'designation': designation
                        })
                elif rel == 'Item_DeviceGraphicCard':
                    graphics = fetch_device_data(session_token, config.glpi_url, href)
                    for graphic in graphics:
                        designation = fetch_designation_from_rel(session_token, config.glpi_url, graphic, 'DeviceGraphicCard')
                        computer_info['itemgraphic'].append({
                            'id': graphic['id'],
                            'memory': graphic.get('memory'),
                            'serial': graphic.get('serial', ''),
                            'designation': designation
                        })
            
            asset_category_id = determine_asset_category_id(computer_info['computertypes_id'], config.category_mapping)
            manufacturer_id = check_manufacturer_in_snipe_it(config.snipe_it_url, config.snipe_it_token, manufacturer_name) or create_manufacturer_in_snipe_it(config.snipe_it_url, config.snipe_it_token, manufacturer_name) or 1
            model_id = check_model_in_snipe_it(config.snipe_it_url, config.snipe_it_token, model_name, asset_category_id, manufacturer_id) or create_model_in_snipe_it(config.snipe_it_url, config.snipe_it_token, model_name, asset_category_id, manufacturer_id) or 1
            asset_id = get_asset_id(config.snipe_it_url, config.snipe_it_token, computer_info['name']) or create_asset_in_snipe_it(config.snipe_it_url, config.snipe_it_token, computer_info, model_id, asset_category_id)
            log_message("Completed importing data from GLPI to Snipe-IT")
        except Exception as e:
            log_message(f"Lỗi: {str(e)}")

    threading.Thread(target=run_import).start()
    return jsonify({'message': 'Đang xử lý import...', 'logs': logs[-10:]})
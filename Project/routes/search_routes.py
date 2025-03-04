from flask import Blueprint, request, jsonify
import config
from utils.snipe_it_utils import *
from utils.logging_utils import *

bp = Blueprint('search', __name__)

@bp.route('/search_asset', methods=['POST'])
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
    
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {config.snipe_it_token}'}
    url = f"{config.snipe_it_url}/hardware?search={asset_tag}&search_field=serial"
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
from flask import Blueprint, request, jsonify
import config
from utils.snipe_it_utils import *
from utils.logging_utils import *

bp = Blueprint('utils', __name__)

@bp.route('/get_categories', methods=['GET'])
def get_categories():
    categories = fetch_categories_from_snipe_it(config.snipe_it_url, config.snipe_it_token)
    log_message(f"Các danh mục tài sản được tải từ ITAM: {len(categories)} items")
    return jsonify({'categories': [cat['name'] for cat in categories]})

@bp.route('/get_status_labels', methods=['GET'])
def get_status_labels():
    status_labels = fetch_status_labels_from_snipe_it(config.snipe_it_url, config.snipe_it_token)
    return jsonify({'status_labels': [f"{status['name']} (ID: {status['id']})" for status in status_labels]})
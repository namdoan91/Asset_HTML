from flask import Flask, render_template
from utils.logging_utils import logs
import config

app = Flask(__name__)

# Khởi tạo các biến toàn cục từ config
glpi_url = config.glpi_url
user_token = config.user_token
app_token = config.app_token
snipe_it_url = config.snipe_it_url
snipe_it_token = config.snipe_it_token
categories = config.categories
category_mapping = config.category_mapping

# Import và đăng ký Blueprints từ routes/
from routes.glpi_routes import bp as glpi_bp
from routes.manual_routes import bp as manual_bp
from routes.search_routes import bp as search_bp
from routes.utils_routes import bp as utils_bp

app.register_blueprint(glpi_bp)
app.register_blueprint(manual_bp)
app.register_blueprint(search_bp)
app.register_blueprint(utils_bp)

@app.route('/')
def home():
    return render_template('index.html', logs=logs)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
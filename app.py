import os
import logging
import requests
import fitz  # PyMuPDF
from flask import Flask, request, jsonify, render_template
from io import BytesIO
import base64
from PIL import Image as PILImage

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB
# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Path to store uploaded PDFs
UPLOAD_FOLDER = 'uploads/'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# DeepInfra API key and base URL for interacting with models
DEEP_INFRA_API_KEY = "your_deep_infra_api_key"
BASE_URL = "https://api.deepinfra.com/v1/openai"




@app.route('/')
def index():
    return render_template('index.html')






if __name__ == "__main__":
    app.run(debug=True)

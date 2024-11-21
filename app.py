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


def extract_text_from_pdf(pdf_file: bytes) -> str:
    try:
        doc = fitz.open(stream=pdf_file, filetype="pdf")
        text = "".join([page.get_text("text") for page in doc])
        return text
    except Exception as e:
        logger.error(f"Error extracting text: {e}")
        return ""


def extract_key_concepts(text: str) -> list:
    try:
        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {DEEP_INFRA_API_KEY}"},
            json={
                "model": "mistralai/Mistral-7B-Instruct-v0.1",
                "messages": [{"role": "user", "content": f"Extract key concepts from this text:\n\n{text}"}],
            },
        )
        response.raise_for_status()
        data = response.json()
        return data.get('choices', [])[0].get('message', {}).get('content', [])
    except Exception as e:
        logger.error(f"Error extracting key concepts: {e}")
        return []


def generate_lesson_plan(extracted_text: str) -> str:
    prompt = f"""
    Based on the following content:

    {extracted_text}

    Please generate a comprehensive lesson plan with the following sections:

    - Introduction
    - Main Body
    - Class Activity
    """
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {DEEP_INFRA_API_KEY}"},
            json={"model": "meta-llama/Meta-Llama-3-70B-Instruct", "messages": [{"role": "user", "content": prompt}]},
        )
        response.raise_for_status()
        lesson_plan = response.json()['choices'][0]['message']['content'].strip()
        return lesson_plan
    except Exception as e:
        logger.error(f"Error generating lesson plan: {e}")
        return ""


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filename)

    # Extract text from the uploaded PDF
    with open(filename, "rb") as f:
        extracted_text = extract_text_from_pdf(f.read())

    if extracted_text:
        key_concepts = extract_key_concepts(extracted_text)
        return jsonify({'extracted_text': extracted_text, 'key_concepts': key_concepts})
    else:
        return jsonify({'error': 'Error extracting text from the PDF'}), 400


@app.route('/generate_lesson_plan', methods=['POST'])
def generate_lesson():
    extracted_text = request.json.get('extracted_text')
    if not extracted_text:
        return jsonify({'error': 'No extracted text provided'}), 400

    lesson_plan = generate_lesson_plan(extracted_text)
    if lesson_plan:
        return jsonify({'lesson_plan': lesson_plan})
    else:
        return jsonify({'error': 'Error generating lesson plan'}), 400


if __name__ == "__main__":
    app.run(debug=True)

import os
import openai
import time
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from browser import get_driver, close_driver
from messenger import send_message, replace_placeholders
from file_handler import get_all_files
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import base64
import hashlib
import logging
import shutil

logging.basicConfig(level=logging.INFO)

load_dotenv()

app = Flask(__name__, template_folder="../app/templates", static_folder="../app/static")

USER_HOME = os.path.expanduser("~")
UPLOAD_FOLDER = os.path.join(USER_HOME, 'whatsapp_attachments')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("La variable de entorno OPENAI_API_KEY no está definida")
openai.api_key = api_key

browser = None

# Ruta para el archivo de autorización
AUTH_FILE_PATH = os.path.join(USER_HOME, '.whatsapp_sender_auth')
AUTH_KEY = 'Epeinado0977'
ENCRYPTION_KEY = hashlib.sha256('0123456789abcdef'.encode()).digest()

CONTACTS_FILE = os.path.join(USER_HOME, 'contacts.json')

def encrypt(text):
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(ENCRYPTION_KEY), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(text.encode()) + padder.finalize()
    
    encrypted = encryptor.update(padded_data) + encryptor.finalize()
    return base64.b64encode(iv + encrypted).decode('utf-8')

def decrypt(encrypted_text):
    encrypted_data = base64.b64decode(encrypted_text)
    iv = encrypted_data[:16]
    cipher = Cipher(algorithms.AES(ENCRYPTION_KEY), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    
    padded_data = decryptor.update(encrypted_data[16:]) + decryptor.finalize()
    
    unpadder = padding.PKCS7(128).unpadder()
    data = unpadder.update(padded_data) + unpadder.finalize()
    return data.decode('utf-8')

def generate_auth_file():
    encrypted_data = encrypt(AUTH_KEY)
    with open(AUTH_FILE_PATH, 'w') as auth_file:
        auth_file.write(encrypted_data)

def check_auth_file():
    if not os.path.exists(AUTH_FILE_PATH):
        return False
    with open(AUTH_FILE_PATH, 'r') as auth_file:
        stored_data = auth_file.read()
        try:
            decrypted_data = decrypt(stored_data)
            return decrypted_data == AUTH_KEY
        except Exception as e:
            print(f"Error during decryption or verification: {e}")
            return False

def load_contacts():
    if os.path.exists(CONTACTS_FILE):
        with open(CONTACTS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_contacts(contacts):
    with open(CONTACTS_FILE, 'w') as f:
        json.dump(contacts, f)

@app.route('/')
def index():
    if not check_auth_file():
        return redirect(url_for('auth'))
    return render_template('index.html')

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    if request.method == 'POST':
        key = request.form.get('authKey')
        if key == AUTH_KEY:
            generate_auth_file()
            return redirect(url_for('index'))
        else:
            return "Clave de instalación incorrecta", 401
    return '''
        <form method="post">
            <label for="authKey">Ingrese la clave de instalación</label>
            <input id="authKey" name="authKey" type="password" />
            <button type="submit">Enviar</button>
        </form>
    '''

@app.route('/correct_text', methods=['POST'])
def correct_text():
    data = request.json
    original_text = data['text']
    has_curly_braces = "{nombre}" in original_text
    has_square_braces = "[nombre]" in original_text

    if has_curly_braces or has_square_braces:
        safe_placeholder = "PLACEHOLDER_NOMBRE"
        safe_text = original_text.replace("{nombre}", safe_placeholder).replace("[nombre]", safe_placeholder)
        prompt = f"Corrige el siguiente texto sin agregar ningún comentario adicional y mantén '{safe_placeholder}' sin cambios: {safe_text}"
    else:
        safe_text = original_text
        prompt = f"Corrige el siguiente texto sin agregar ningún comentario adicional: {safe_text}"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un asistente de redacción que mejora la coherencia y amabilidad de los textos."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        improved_text = response.choices[0]['message']['content'].strip()

        if has_curly_braces:
            improved_text = improved_text.replace("PLACEHOLDER_NOMBRE", "{nombre}")
        if has_square_braces:
            improved_text = improved_text.replace("PLACEHOLDER_NOMBRE", "[nombre]")

        return jsonify({'corrected_text': improved_text})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/send_messages', methods=['POST'])
def send_messages_route():
    global browser
    data = request.json
    final_text = data['final_text']
    recipients = data['recipients']
    folder_path = data.get('folder_path')

    browser = get_driver()

    try:
        total_messages = len(recipients)
        for i, recipient in enumerate(recipients):
            message = replace_placeholders(final_text, recipient)
            attachment_paths = get_all_files(folder_path) if folder_path else []
            send_message(browser, recipient['phone'], message, attachment_paths, i, total_messages, i == total_messages - 1)
        
        return jsonify({'status': 'Messages sent'})
    except Exception as e:
        return jsonify({'error': str(e)})
    # No cerramos el navegador aquí
    # finally:
    #     close_driver()  # No cerramos el navegador en el bloque finally

@app.route('/close_browser', methods=['POST'])
def close_browser():
    close_driver()
    # Borrar la carpeta y sus archivos
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        shutil.rmtree(app.config['UPLOAD_FOLDER'])
        logging.info(f"Carpeta {app.config['UPLOAD_FOLDER']} borrada.")
    return jsonify({'status': 'Browser closed and folder deleted'})

@app.route('/upload_files', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return jsonify({'error': 'No files part in the request'}), 400
    
    files = request.files.getlist('files')
    if not files:
        return jsonify({'error': 'No files uploaded'}), 400

    upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(files[0].filename.split('/')[0]))
    os.makedirs(upload_dir, exist_ok=True)
    
    for file in files:
        filename = secure_filename(file.filename)
        file.save(os.path.join(upload_dir, filename))
    
    return jsonify({'upload_path': upload_dir})

@app.route('/save_contacts', methods=['POST'])
def save_contacts_route():
    contacts = request.json.get('contacts', [])
    save_contacts(contacts)
    return jsonify({'status': 'Contacts saved'})

@app.route('/load_contacts', methods=['GET'])
def load_contacts_route():
    contacts = load_contacts()
    return jsonify({'contacts': contacts})

if __name__ == '__main__':
    # Crear el archivo contacts.json si no existe
    if not os.path.exists(CONTACTS_FILE):
        with open(CONTACTS_FILE, 'w') as f:
            json.dump([], f)
    
    app.run(debug=True, port=3000)

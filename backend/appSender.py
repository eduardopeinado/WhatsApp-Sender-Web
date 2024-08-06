import os
import openai
import time
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from browser import get_driver, close_driver
from messenger import send_message, replace_placeholders
from file_handler import get_all_files
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import logging
import shutil
from sqlalchemy.exc import IntegrityError

logging.basicConfig(level=logging.INFO)

load_dotenv()

# Define la raíz del proyecto usando el directorio de trabajo actual
PROJECT_ROOT = os.getcwd()
TEMPLATES_FOLDER = os.path.join(PROJECT_ROOT, 'app', 'templates')
STATIC_FOLDER = os.path.join(PROJECT_ROOT, 'app', 'static')

# Imprimir las rutas para verificar
print(f"Project Root: {PROJECT_ROOT}")
print(f"Templates Folder: {TEMPLATES_FOLDER}")
print(f"Static Folder: {STATIC_FOLDER}")

app = Flask(__name__, template_folder=TEMPLATES_FOLDER, static_folder=STATIC_FOLDER)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(PROJECT_ROOT, "backend/instance/site.db")}'
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Asegurarse de que el directorio de la base de datos exista
db_path = os.path.join(PROJECT_ROOT, 'backend/instance/site.db')
db_dir = os.path.dirname(db_path)
if not os.path.exists(db_dir):
    os.makedirs(db_dir)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

USER_HOME = os.path.expanduser("~")
UPLOAD_FOLDER = os.path.join(USER_HOME, 'whatsapp_attachments')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("La variable de entorno OPENAI_API_KEY no está definida")
openai.api_key = api_key

browser = None

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    temp_password = db.Column(db.String(60), nullable=True)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    first_name = db.Column(db.String(30), nullable=False)
    last_name = db.Column(db.String(30), nullable=False)
    medium = db.Column(db.String(30), nullable=False)
    send = db.Column(db.String(10), nullable=False)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].lower()
        temp_password = request.form['temp_password']
        hashed_temp_password = bcrypt.generate_password_hash(temp_password).decode('utf-8')
        user = User(username=username, password=hashed_temp_password, temp_password=hashed_temp_password)
        db.session.add(user)
        try:
            db.session.commit()
            flash('User registered successfully!', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('Username already exists. Please choose a different username.', 'danger')
            return redirect(url_for('register'))
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].lower()
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user:
            if user.temp_password and bcrypt.check_password_hash(user.temp_password, password):
                session['user_id'] = user.id
                return redirect(url_for('change_password'))
            elif bcrypt.check_password_hash(user.password, password):
                session['user_id'] = user.id
                return redirect(url_for('index'))
        flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html')

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if new_password == confirm_password:
            hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
            user = User.query.get(session['user_id'])
            user.password = hashed_password
            user.temp_password = None
            db.session.commit()
            flash('Your password has been updated!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Passwords do not match. Please try again.', 'danger')
    
    return render_template('change_password.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

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
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    contacts = request.json.get('contacts', [])

    # Borrar contactos existentes del usuario
    Contact.query.filter_by(user_id=user_id).delete()

    # Guardar nuevos contactos
    for contact in contacts:
        new_contact = Contact(
            user_id=user_id,
            phone=contact['phone'],
            first_name=contact['first_name'],
            last_name=contact['last_name'],
            medium=contact['medium'],
            send=contact['send']
        )
        db.session.add(new_contact)
    db.session.commit()

    return jsonify({'status': 'Contacts saved'})

@app.route('/load_contacts', methods=['GET'])
def load_contacts_route():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    contacts = Contact.query.filter_by(user_id=user_id).all()
    contacts_data = [
        {
            'phone': contact.phone,
            'first_name': contact.first_name,
            'last_name': contact.last_name,
            'medium': contact.medium,
            'send': contact.send
        } for contact in contacts
    ]

    return jsonify({'contacts': contacts_data})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=3000)

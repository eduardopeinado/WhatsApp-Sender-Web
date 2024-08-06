import os
import sys
from dotenv import load_dotenv
import webview
from threading import Thread

# Obtener la ruta absoluta al directorio actual
base_path = os.path.dirname(os.path.abspath(__file__))

# Revisar si estamos en el entorno de ejecución PyInstaller
if getattr(sys, 'frozen', False):
    # Estamos en un entorno de PyInstaller
    base_path = sys._MEIPASS
    print(f"Running in PyInstaller environment. _MEIPASS: {sys._MEIPASS}")

# Agregar la carpeta 'backend' al sys.path
backend_path = os.path.join(base_path, 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Cargar el archivo .env
dotenv_path = os.path.join(base_path, '.env')
if not os.path.exists(dotenv_path):
    dotenv_path = os.path.join(backend_path, '.env')

print(".env path:", dotenv_path)  # Línea de depuración para imprimir dotenv_path

load_dotenv(dotenv_path)

print("base_path:", base_path)
print("backend_path:", backend_path)
print("sys.path:", sys.path)

try:
    from appSender import app
except ImportError as e:
    print(f"Error importing appSender: {e}")
    sys.exit(1)

def start_server():
    app.run(debug=False, port=3000)

if __name__ == "__main__":
    server_thread = Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()

    # Crear la ventana del navegador con tamaño personalizado
    webview.create_window("WhatsApp Sender", "http://127.0.0.1:3000", width=1200, height=768)

    # Ejecutar la aplicación de la ventana del navegador
    webview.start()

    # Detener el servidor Flask cuando se cierra la ventana del navegador
    sys.exit()

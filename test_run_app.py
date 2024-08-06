import os
import sys

# Obtener la ruta absoluta al directorio actual
base_path = os.path.dirname(os.path.abspath(__file__))

# Agregar la carpeta 'backend' al sys.path
backend_path = os.path.join(base_path, 'backend')
sys.path.append(backend_path)

try:
    from app import app
except ImportError as e:
    print(f"Error importing app: {e}")
    sys.exit(1)

if __name__ == "__main__":
    app.run(debug=False, port=3000)

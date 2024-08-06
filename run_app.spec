# run_app.spec
import os
from PyInstaller.utils.hooks import collect_submodules

base_path = os.path.abspath('.')
backend_path = os.path.join(base_path, 'backend')
app_path = os.path.join(base_path, 'app')
templates_path = os.path.join(app_path, 'templates')
static_path = os.path.join(app_path, 'static')
assets_path = os.path.join(app_path, 'assets')
env_file = os.path.join(backend_path, '.env')

block_cipher = None

# Collect submodules for all dependencies
hiddenimports = (collect_submodules('flask') + 
                 collect_submodules('openai') + 
                 collect_submodules('selenium') + 
                 collect_submodules('webdriver_manager') + 
                 collect_submodules('aiohttp') + 
                 collect_submodules('aiosignal') + 
                 collect_submodules('altgraph') + 
                 collect_submodules('annotated_types') + 
                 collect_submodules('anyio') + 
                 collect_submodules('appscript') + 
                 collect_submodules('attrs') + 
                 collect_submodules('blinker') + 
                 collect_submodules('certifi') + 
                 collect_submodules('cffi') + 
                 collect_submodules('charset_normalizer') + 
                 collect_submodules('click') + 
                 collect_submodules('cryptography') + 
                 collect_submodules('distro') + 
                 collect_submodules('et_xmlfile') + 
                 collect_submodules('frozenlist') + 
                 collect_submodules('h11') + 
                 collect_submodules('httpcore') + 
                 collect_submodules('httpx') + 
                 collect_submodules('idna') + 
                 collect_submodules('itsdangerous') + 
                 collect_submodules('Jinja2') + 
                 collect_submodules('lxml') + 
                 collect_submodules('macholib') + 
                 collect_submodules('MarkupSafe') + 
                 collect_submodules('multidict') + 
                 collect_submodules('openpyxl') + 
                 collect_submodules('outcome') + 
                 collect_submodules('packaging') + 
                 collect_submodules('psutil') + 
                 collect_submodules('pycparser') + 
                 collect_submodules('pydantic') + 
                 collect_submodules('pydantic_core') + 
                 collect_submodules('pyinstaller') + 
                 collect_submodules('pyinstaller_hooks_contrib') + 
                 collect_submodules('PySocks') + 
                 collect_submodules('python_dotenv') + 
                 collect_submodules('requests') + 
                 collect_submodules('setuptools') + 
                 collect_submodules('sniffio') + 
                 collect_submodules('sortedcontainers') + 
                 collect_submodules('tqdm') + 
                 collect_submodules('trio') + 
                 collect_submodules('trio_websocket') + 
                 collect_submodules('typing_extensions') + 
                 collect_submodules('urllib3') + 
                 collect_submodules('websocket_client') + 
                 collect_submodules('Werkzeug') + 
                 collect_submodules('wsproto') + 
                 collect_submodules('xlwings') + 
                 collect_submodules('yarl') +
                 collect_submodules('webview'))

datas = [
    (templates_path, 'app/templates'),
    (os.path.join(static_path, 'styles.css'), 'app/static'),
    (os.path.join(static_path, 'images'), 'app/static/images'),
    (os.path.join(static_path, 'sounds'), 'app/static/sounds'),
    (os.path.join(assets_path, 'icons'), 'app/assets/icons'),
    (env_file, '.env'),  # Ensure this is treated as a file
    (backend_path, 'backend')
]

a = Analysis(
    ['run_app.py'],
    pathex=[base_path],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='WhatsAppSender',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False  # Asegúrate de que la consola no se muestre
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WhatsAppSender'
)

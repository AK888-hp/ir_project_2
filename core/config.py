import os

# --- Directory Setup (Minimal) ---
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) 
STATIC_DIR = os.path.join(BASE_DIR, 'static')
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)
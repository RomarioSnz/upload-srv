from waitress import serve
from main import app  # из main.py

serve(app, host='0.0.0.0', port=8000)

import os
from flask import Flask
from dotenv import load_dotenv
try:
    from .donations import donations_bp  # when run as a module: python -m backend.app
except ImportError:
    from donations import donations_bp  # when run as a script from backend/: python app.py

load_dotenv()

app = Flask(__name__)

# Donations API
app.register_blueprint(donations_bp, url_prefix="/api")

if __name__ == "__main__":
    print("Starting Flask app on port 5000...")
    print("Database URL:", os.getenv("DATABASE_URL", "Not set"))
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)), debug=True)

import os
from flask import Flask
from dotenv import load_dotenv

from .donations import donations_bp  # use relative import when running as module

load_dotenv()

app = Flask(__name__)

# Root route
@app.route("/")
def index():
    return {"message": "Flask backend is running. Use /api for endpoints."}

# Donations API
app.register_blueprint(donations_bp, url_prefix="/api")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", 5000)), debug=True)

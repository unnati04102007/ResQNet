import sqlite3
from flask import Flask, render_template, request, redirect, url_for, g

app = Flask(__name__)
DATABASE = "../database/resqnet.db"   # database file path

# -------------------
# Database Connection
# -------------------
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with open("../database/schema.sql", "r") as f:
            db.executescript(f.read())
        db.commit()

# -------------------
# Routes 
# -------------------

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password").strip()

        # 🔍 Debug prints
        print("🔍 Input:", username, password)

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()

        # 🔍 Debug result
        print("🔍 Query Result:", user)

        if user:
            return f"✅ Welcome back, {username}!"
        else:
            return "❌ Invalid username or password."
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            return "❌ Passwords do not match!"

        db = get_db()
        cursor = db.cursor()

        cursor.execute("SELECT * FROM users WHERE username=? OR email=?", (username, email))
        existing_user = cursor.fetchone()

        if existing_user:
            return "❌ Username or Email already exists!"

        cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                       (username, email, password))
        db.commit()

        return redirect(url_for("login"))

    return render_template("register.html")


if __name__ == "__main__":
    #init_db()   # create tables if not exists
    app.run(debug=True)

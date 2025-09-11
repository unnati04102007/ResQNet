import sqlite3
from flask import Flask, render_template, request, redirect, url_for, g
from werkzeug.security import generate_password_hash, check_password_hash  # ✅ secure password handling

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

# -------------------
# LOGIN
# -------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        db = get_db()
        cursor = db.cursor()

        # ✅ fetch stored hashed password for this user
        cursor.execute("SELECT password FROM users WHERE username=?", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user[0], password):  
            # ✅ verify entered password with stored hash
            return f"✅ Welcome back, {username}!"
        else:
            return "❌ Invalid username or password."
    return render_template("login.html")

# -------------------
# REGISTER
# -------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        # ✅ hash password before saving
        hashed_pw = generate_password_hash(password)

        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)", 
                (username, email, hashed_pw)
            )
            db.commit()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return "❌ Username or Email already exists!"
    return render_template("register.html")

# -------------------
# MAIN
# -------------------
if __name__ == "__main__":
    # init_db()   # disable just for testing
    app.run(debug=True)
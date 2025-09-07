import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, g, flash
from werkzeug.security import generate_password_hash, check_password_hash

# --- Flask Setup ---
app = Flask(__name__)
app.secret_key = "supersecretkey"   # change later, keep private

# --- Database Path ---
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE = os.path.join(ROOT, "database", "resqnet.db")

# --- Database Connection ---
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.execute("PRAGMA foreign_keys = ON;")
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

# ==============================
# USER AUTH ROUTES
# ==============================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]

        if not username or not email or not password:
            flash("All fields required")
            return redirect(url_for("register"))

        db = get_db()
        cur = db.cursor()

        # hash password before storing
        hashed_pw = generate_password_hash(password)

        try:
            cur.execute(
                "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
                (username, email, hashed_pw, "citizen")
            )
            db.commit()
            flash("✅ Registered successfully! Please log in.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("⚠️ Username or Email already exists.")
            return redirect(url_for("register"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"]

        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cur.fetchone()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            flash(f"👋 Welcome {user['username']}!")
            return redirect(url_for("dashboard"))
        else:
            flash("❌ Invalid email or password")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You’ve been logged out.")
    return redirect(url_for("login"))

# ==============================
# BASIC DASHBOARD
# ==============================

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", user=session)

# ==============================
# REPORT ROUTES (basic)
# ==============================

@app.route("/report", methods=["GET","POST"])
def create_report():
    if "user_id" not in session:
        flash("Login required to file a report.")
        return redirect(url_for("login"))

    if request.method=="POST":
        title = request.form["title"]
        description = request.form["description"]

        db = get_db()
        cur = db.cursor()
        cur.execute(
            "INSERT INTO disaster_reports (user_id, title, description, disaster_type, severity) VALUES (?,?,?,?,?)",
            (session["user_id"], title, description, "general", 3)
        )
        db.commit()
        flash("✅ Report submitted!")
        return redirect(url_for("dashboard"))

    return render_template("report_form.html")

@app.route("/admin/reports")
def view_reports():
    if "role" not in session or session["role"] != "admin":
        flash("Admins only.")
        return redirect(url_for("dashboard"))

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM disaster_reports ORDER BY created_at DESC")
    reports = cur.fetchall()
    return render_template("admin_reports.html", reports=reports)

# ==============================
# RUN APP
# ==============================

if __name__ == "__main__":
    app.run(debug=True)

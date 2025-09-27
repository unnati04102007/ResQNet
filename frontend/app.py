from flask import Flask, render_template

# Point Flask to use the current folder for templates and static files
app = Flask(__name__, template_folder='.', static_folder='.', static_url_path='')

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/report")
def report():
    return render_template("report.html")

@app.route("/donation")
def donation():
    return render_template("donation.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/register")
def register():
    return render_template("register.html")

if __name__ == "__main__":
    app.run(debug=True)

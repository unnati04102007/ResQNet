import sqlite3, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "database", "resqnet.db")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Create users table
cur.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT DEFAULT 'citizen'
);''')

# Create volunteers table
cur.execute('''CREATE TABLE IF NOT EXISTS volunteers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    bio TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id)
);''')

# Create disaster_reports table
cur.execute('''CREATE TABLE IF NOT EXISTS disaster_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    disaster_type TEXT NOT NULL,
    severity INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);''')

conn.commit()
print("✅ All tables created successfully")
conn.close()
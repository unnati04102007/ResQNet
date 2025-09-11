import sqlite3
import os

# Ensure database folder exists
db_path = os.path.join("..", "database", "resqnet.db")
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# Connect to database (this will create resqnet.db if it doesn't exist)
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create users table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
);
""")

# Insert a test user
cursor.execute("""
INSERT OR IGNORE INTO users (username, email, password)
VALUES ('testuser', 'test@example.com', '1234');
""")

conn.commit()
conn.close()

print("✅ Database and users table created at:", db_path)
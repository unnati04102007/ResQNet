import sqlite3, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "database", "resqnet.db")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# insert test user
cur.execute("INSERT OR IGNORE INTO users (username,email,password,role) VALUES (?,?,?,?)",
            ("testuser","test@example.com","1234","citizen"))

# insert volunteer user & volunteer profile
cur.execute("INSERT OR IGNORE INTO users (username,email,password,role) VALUES (?,?,?,?)",
            ("vol1","vol1@example.com","volpass","volunteer"))
conn.commit()

cur.execute("SELECT id FROM users WHERE username='vol1'")
vol_user_id = cur.fetchone()[0]
cur.execute("INSERT OR IGNORE INTO volunteers (user_id, bio) VALUES (?,?)", (vol_user_id, "I help with rescues"))
conn.commit()

# insert a test report by testuser
cur.execute("SELECT id FROM users WHERE username='testuser'")
uid = cur.fetchone()[0]
cur.execute("INSERT INTO disaster_reports (user_id, title, description, disaster_type, severity) VALUES (?,?,?,?,?)",
            (uid, "Bridge flood", "Bridge washed away near x", "flood", 4))
conn.commit()
print("✅ Seeded sample data")
conn.close()

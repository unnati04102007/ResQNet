import os
import sqlite3

RESET_DB = False   # <- Set True to delete existing DB and rebuild (dev only!)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # goes up from backend/
DB_PATH = os.path.join(ROOT, "database", "resqnet.db")
SCHEMA_PATH = os.path.join(ROOT, "database", "schema.sql")

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

if RESET_DB and os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print("🗑️ Deleted existing DB for reset.")

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON;")

with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
    sql = f.read()
conn.executescript(sql)
conn.commit()
conn.close()
print("✅ Database initialized at:", DB_PATH)

import sqlite3
import os

db_path = 'db.sqlite3'
if not os.path.exists(db_path):
    print(f"Database file {db_path} not found.")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'scanner_%';")
    tables = cursor.fetchall()
    print("Scanner tables found:")
    for table in tables:
        print(table[0])
    conn.close()

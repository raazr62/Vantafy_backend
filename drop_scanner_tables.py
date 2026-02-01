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
    print("Dropping tables:")
    for table in tables:
        table_name = table[0]
        print(f"- {table_name}")
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
    
    conn.commit()
    conn.close()
    print("Done.")

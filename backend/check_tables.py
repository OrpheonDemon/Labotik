import sqlite3
conn = sqlite3.connect('labotik.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print("Tablas encontradas:")
for t in tables:
    print(f"  - {t}")
    cursor.execute(f"PRAGMA table_info({t})")
    cols = cursor.fetchall()
    for col in cols:
        print(f"      {col[1]} ({col[2]})")
conn.close()
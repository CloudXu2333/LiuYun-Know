
import sqlite3
import os

db_path = r'd:\Desktop\learn\ppt\LiuYun-know\LiuYun-Know\banana-slides\backend\instance\database.db'

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
try:
    # Check if column exists
    cursor.execute("PRAGMA table_info(projects)")
    columns = [info[1] for info in cursor.fetchall()]
    if 'user_id' in columns:
        print("Column user_id already exists.")
    else:
        print("Adding user_id column...")
        cursor.execute("ALTER TABLE projects ADD COLUMN user_id VARCHAR(100)")
        cursor.execute("CREATE INDEX ix_projects_user_id ON projects (user_id)")
        conn.commit()
        print("Column added successfully.")
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()

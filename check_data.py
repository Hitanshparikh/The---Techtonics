import sqlite3
import os

# Check coastal_data.db
db_path = os.path.join('backend', 'coastal_data.db')
if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("Tables:", tables)
        
        # Check coastal_data count
        cursor.execute("SELECT COUNT(*) FROM coastal_data")
        count = cursor.fetchone()[0]
        print(f"Total coastal_data records: {count}")
        
        if count > 0:
            cursor.execute("SELECT * FROM coastal_data LIMIT 3")
            print("Sample records:")
            for row in cursor.fetchall():
                print(row)
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
else:
    print("Database file not found")

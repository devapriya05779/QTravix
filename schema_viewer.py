import sqlite3

def get_schema():
    conn = sqlite3.connect('instance/qtravix.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    
    
    for table in tables:
        print(f"\nTable: {table}")
        cursor.execute(f"PRAGMA table_info({table})")
        for col in cursor.fetchall():
            print(col)
            
    conn.close()

if __name__ == "__main__":
    get_schema()

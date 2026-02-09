import mysql.connector
from config import Config

def deep_inspect():
    print(f"Connecting to {Config.MYSQL_HOST}:{Config.MYSQL_PORT} as {Config.MYSQL_USER}...")
    try:
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            port=Config.MYSQL_PORT
        )
        cursor = conn.cursor()
        
        # 1. Check Data Directory
        cursor.execute("SHOW VARIABLES LIKE 'datadir'")
        datadir = cursor.fetchone()
        print(f"\n[SERVER CONFIG] Data Directory: {datadir[1]}")
        
        # 2. Check Port
        cursor.execute("SHOW VARIABLES LIKE 'port'")
        port = cursor.fetchone()
        print(f"[SERVER CONFIG] Port: {port[1]}")
        
        # 3. List All Databases again
        cursor.execute("SHOW DATABASES")
        dbs = [x[0] for x in cursor.fetchall()]
        print(f"\n[DB LISTING] Total Databases Found: {len(dbs)}")
        print(dbs)
        
        # 4. Check 'hackathon_db' tables (Reference check)
        if 'hackathon_db' in dbs:
            conn.database = 'hackathon_db'
            cursor.execute("SHOW TABLES")
            tables = [x[0] for x in cursor.fetchall()]
            print(f"\n[REFERENCE CHECK] Tables in 'hackathon_db': {tables[:3]} (showing first 3)")
        
        # 5. Create a '00_DEBUG_PLEASE_DELETE' database to test visibility at top of list
        print("\n[TEST] Creating database '00_aa_debug_top'...")
        cursor.execute("CREATE DATABASE IF NOT EXISTS 00_aa_debug_top")
        print("[TEST] Created using Python.")
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    deep_inspect()
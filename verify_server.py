import mysql.connector
from config import Config

def verify_server():
    print("--- Verifying MySQL Server State ---")
    try:
        # Connect without selecting a database to list all DBs
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            port=Config.MYSQL_PORT
        )
        cursor = conn.cursor()
        
        # List Databases
        cursor.execute("SHOW DATABASES")
        dbs = [db[0] for db in cursor.fetchall()]
        print(f"Existing Databases: {dbs}")
        
        target_db = 'smart_attendance_system'
        
        if target_db in dbs:
            print(f"\n[OK] Database '{target_db}' FOUND.")
            # Check Tables
            conn.database = target_db
            cursor.execute("SHOW TABLES")
            tables = [t[0] for t in cursor.fetchall()]
            print(f"Tables in '{target_db}': {tables}")
            
            # Check if expected tables exist
            expected = ['universities', 'admins', 'faculty', 'students', 'attendance']
            missing = [t for t in expected if t not in tables]
            if missing:
                print(f"[WARN] Missing expected tables: {missing}")
            else:
                print("[SUCCESS] All core tables appear to present.")
        else:
            print(f"\n[ERROR] Database '{target_db}' NOT FOUND.")
            
    except mysql.connector.Error as err:
        print(f"MySQL Error: {err}")
    except Exception as e:
        print(f"General Error: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    verify_server()
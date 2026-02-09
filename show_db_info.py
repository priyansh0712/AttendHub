import mysql.connector
from config import Config
import sys

def show_info():
    print(f"\n{'='*50}")
    print("PYTHON CONNECTION DETAILS")
    print(f"{'='*50}")
    print(f"Host:     {Config.MYSQL_HOST}")
    print(f"Port:     {Config.MYSQL_PORT}")
    print(f"User:     {Config.MYSQL_USER}")
    print(f"Database: {Config.MYSQL_DATABASE}")
    print(f"{'='*50}\n")
    
    try:
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            port=Config.MYSQL_PORT
        )
        cursor = conn.cursor()
        
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        print(f"Server Version: {version}")
        
        cursor.execute("SHOW DATABASES")
        dbs = [x[0] for x in cursor.fetchall()]
        print("\nAVAILABLE DATABASES ON THIS SERVER:")
        print("-" * 35)
        found = False
        for db in dbs:
            marker = "  <-- HERE IT IS!" if db == Config.MYSQL_DATABASE else ""
            print(f" - {db}{marker}")
            if db == Config.MYSQL_DATABASE:
                found = True
        
        print("-" * 35)
        
        if found:
            print(f"\n[SUCCESS] The database '{Config.MYSQL_DATABASE}' DEFINITELY exists on localhost:{Config.MYSQL_PORT}")
            print("If you cannot see it in your GUI tool (Workbench/HeidiSQL/phpMyAdmin):")
            print("1. Right-click the connection and hit 'Refresh' or 'Reload'")
            print(f"2. Ensure your tool is connected to port {Config.MYSQL_PORT}")
            print(f"3. Ensure your tool is logged in as '{Config.MYSQL_USER}'")
        else:
            print(f"\n[ERROR] The database '{Config.MYSQL_DATABASE}' is MISSING.")
            
    except mysql.connector.Error as err:
        print(f"\n[CONNECTION FAILED] Could not connect: {err}")

if __name__ == "__main__":
    show_info()
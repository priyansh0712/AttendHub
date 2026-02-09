import mysql.connector
from config import Config

def verify_aa():
    print(f"Checking database: {Config.MYSQL_DATABASE} on {Config.MYSQL_HOST}")
    try:
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            port=Config.MYSQL_PORT,
            database=Config.MYSQL_DATABASE
        )
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = [x[0] for x in cursor.fetchall()]
        print(f"Tables in '{Config.MYSQL_DATABASE}': {tables}")
        
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    verify_aa()
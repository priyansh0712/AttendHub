import mysql.connector
from config import Config

def check_tables():
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
        tables = cursor.fetchall()
        print("Tables in DB:", tables)
    except Exception as e:
        print(e)
    finally:
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    check_tables()

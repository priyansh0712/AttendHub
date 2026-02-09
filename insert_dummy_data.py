
import mysql.connector
from config import Config

def load_dummy_data():
    print(f"Connecting to MySQL at {Config.MYSQL_HOST}...")
    try:
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE
        )
        cursor = conn.cursor()

        print("Reading dummy_data.sql...")
        with open('dummy_data.sql', 'r') as f:
            sql_script = f.read()

        statements = sql_script.split(';')

        print("Inserting dummy data...")
        count = 0
        for statement in statements:
            if statement.strip():
                try:
                    cursor.execute(statement)
                    count += 1
                except mysql.connector.Error as err:
                    print(f"Skipping/Error: {err}")
        
        conn.commit()
        print(f"Done! Executed {count} statements.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    load_dummy_data()

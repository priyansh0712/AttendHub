
import mysql.connector
from config import Config
from datetime import datetime, timedelta

def insert_reports():
    print('Inserting Dummy Reports...')
    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DATABASE,
        port=Config.MYSQL_PORT
    )
    cursor = conn.cursor()

    # Get University ID
    cursor.execute("SELECT university_id FROM universities WHERE domain = 'techuniv.edu.in' LIMIT 1")
    uni = cursor.fetchone()
    if not uni:
        print("Test university not found.")
        return
    
    university_id = uni[0]

    reports = [
        (university_id, 'Monthly Attendance Summary', 'System', 'Last 30 Days', '/reports/att_jan.pdf', datetime.now() - timedelta(days=2)),
        (university_id, 'Faculty Performance Report', 'Admin', 'Fall 2023', '/reports/fac_perf.pdf', datetime.now() - timedelta(days=5)),
        (university_id, 'Student Enrolment Stats', 'Admin', '2024 Batch', '/reports/enrollment.pdf', datetime.now() - timedelta(days=10)),
        (university_id, 'System Usage Logs', 'System', 'January 2026', '/reports/sys_logs.csv', datetime.now() - timedelta(days=15)),
        (university_id, 'Subscription Invoice', 'Finance', 'February 2026', '/reports/inv_feb.pdf', datetime.now() - timedelta(hours=4)),
    ]

    for r in reports:
        sql = """
            INSERT INTO reports 
            (university_id, report_type, generated_by, coverage_period, file_path, created_at) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, r)
    
    conn.commit()
    print('Dummy reports inserted.')
    cursor.close()
    conn.close()

if __name__ == '__main__':
    insert_reports()

import argparse
import hashlib
from datetime import date, timedelta

import mysql.connector

from config import Config


CORE_TABLES_ORDER = [
    # child -> parent
    'attendance',
    'lectures',
    'timetable',
    'students',
    'faculty',
    'admins',
    'reports',
    'universities',
]


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def table_exists(cursor, table_name: str) -> bool:
    cursor.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=%s AND table_name=%s",
        (Config.MYSQL_DATABASE, table_name),
    )
    return int(cursor.fetchone()[0]) > 0


def wipe_all_data(conn) -> None:
    cursor = conn.cursor()
    cursor.execute('SET FOREIGN_KEY_CHECKS=0')

    for table in CORE_TABLES_ORDER:
        if table_exists(cursor, table):
            cursor.execute(f'TRUNCATE TABLE `{table}`')

    cursor.execute('SET FOREIGN_KEY_CHECKS=1')
    conn.commit()


def seed_demo_dataset(conn, *, today: date, admin_password: str, faculty_password: str, student_password: str) -> None:
    cursor = conn.cursor()

    # 1) University
    cursor.execute(
        """
        INSERT INTO universities (university_name, domain, plan, is_active, registered_address, official_contact_email, official_contact_phone, website_url)
        VALUES (%s, %s, %s, TRUE, %s, %s, %s, %s)
        """,
        (
            'Demo University',
            'demo.edu',
            'PREMIUM',
            '123 Demo Street, Demo City',
            'contact@demo.edu',
            '+91-99999-11111',
            'https://demo.edu',
        ),
    )
    university_id = cursor.lastrowid

    # 2) Admin
    cursor.execute(
        """
        INSERT INTO admins (university_id, name, email, password_hash, is_verified)
        VALUES (%s, %s, %s, %s, TRUE)
        """,
        (university_id, 'Demo Admin', 'admin@demo.edu', sha256(admin_password)),
    )

    # 3) Faculty
    faculty_rows = [
        ('Dr. Priya Sharma', 'faculty1@demo.edu', 'Computer Science'),
        ('Prof. Arjun Singh', 'faculty2@demo.edu', 'Information Technology'),
    ]
    faculty_ids = []
    for name, email, dept in faculty_rows:
        cursor.execute(
            """
            INSERT INTO faculty (university_id, name, email, department, password_hash, is_active)
            VALUES (%s, %s, %s, %s, %s, TRUE)
            """,
            (university_id, name, email, dept, sha256(faculty_password)),
        )
        faculty_ids.append(int(cursor.lastrowid))

    faculty1_id, faculty2_id = faculty_ids

    # 4) Students
    students = []

    def add_students(prefix: str, dept: str, sem: int, start_idx: int, count: int):
        for i in range(start_idx, start_idx + count):
            enrollment = f"{prefix}-{i:04d}"
            name = f"{dept.split()[0]} Student {i}"
            email = f"{enrollment.lower()}@demo.edu"
            cursor.execute(
                """
                INSERT INTO students (university_id, enrollment_no, name, department, semester, email, password_hash, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
                """,
                (university_id, enrollment, name, dept, sem, email, sha256(student_password)),
            )
            students.append(int(cursor.lastrowid))

    add_students('DEMO-CS', 'Computer Science', 3, 1, 25)
    add_students('DEMO-IT', 'Information Technology', 5, 1, 15)

    # 5) Timetable (for today's day code)
    day_code = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'][today.weekday()]

    timetable_entries = [
        # faculty_id, dept, sem, subject, start, end
        (faculty1_id, 'Computer Science', 3, 'Data Structures', '10:00:00', '11:00:00'),
        (faculty1_id, 'Computer Science', 3, 'DBMS', '11:00:00', '12:00:00'),
        (faculty2_id, 'Information Technology', 5, 'Computer Networks', '12:00:00', '13:00:00'),
    ]

    timetable_ids = []
    for faculty_id, dept, sem, subject, start_time, end_time in timetable_entries:
        cursor.execute(
            """
            INSERT INTO timetable (university_id, faculty_id, department, semester, subject, day, start_time, end_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (university_id, faculty_id, dept, sem, subject, day_code, start_time, end_time),
        )
        timetable_ids.append(int(cursor.lastrowid))

    # 6) Lectures (today)
    # - First slot: ONGOING, no attendance yet (so Mark Attendance shows 'Mark')
    cursor.execute(
        """
        INSERT INTO lectures (timetable_id, lecture_date, status)
        VALUES (%s, %s, 'ONGOING')
        """,
        (timetable_ids[0], today),
    )

    # - Second slot: ENDED with attendance already marked (so UI shows Preview)
    cursor.execute(
        """
        INSERT INTO lectures (timetable_id, lecture_date, status, ended_at)
        VALUES (%s, %s, 'ENDED', CURRENT_TIMESTAMP)
        """,
        (timetable_ids[1], today),
    )
    ended_lecture_id = int(cursor.lastrowid)

    cs_students = students[:25]
    for idx, student_id in enumerate(cs_students):
        status = 'ABSENT' if (idx % 9 == 0) else 'PRESENT'
        cursor.execute(
            """
            INSERT INTO attendance (lecture_id, student_id, status)
            VALUES (%s, %s, %s)
            """,
            (ended_lecture_id, student_id, status),
        )

    # 7) Past lecture history (ENDED) for reports
    past_dates = [today - timedelta(days=1), today - timedelta(days=3), today - timedelta(days=7)]
    for past_day in past_dates:
        cursor.execute(
            """
            INSERT INTO lectures (timetable_id, lecture_date, status, ended_at)
            VALUES (%s, %s, 'ENDED', CURRENT_TIMESTAMP)
            """,
            (timetable_ids[0], past_day),
        )
        lecture_id = int(cursor.lastrowid)
        for idx, student_id in enumerate(cs_students[:20]):
            status = 'ABSENT' if (idx % 8 == 0) else 'PRESENT'
            cursor.execute(
                """
                INSERT INTO attendance (lecture_id, student_id, status)
                VALUES (%s, %s, %s)
                """,
                (lecture_id, student_id, status),
            )

    conn.commit()


def main():
    parser = argparse.ArgumentParser(description='Wipe all DB data and seed a fresh dummy dataset for testing.')
    parser.add_argument('--yes', action='store_true', help='Skip confirmation prompt')
    parser.add_argument('--admin-password', default='admin123', help='Password for seeded admin')
    parser.add_argument('--faculty-password', default='faculty123', help='Password for seeded faculty')
    parser.add_argument('--student-password', default='student123', help='Password for seeded students')
    args = parser.parse_args()

    if not args.yes:
        print('WARNING: This will DELETE ALL DATA in the configured database:', Config.MYSQL_DATABASE)
        confirm = input("Type 'RESET' to continue: ").strip()
        if confirm != 'RESET':
            print('Aborted.')
            return

    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DATABASE,
    )

    try:
        wipe_all_data(conn)
        seed_demo_dataset(
            conn,
            today=date.today(),
            admin_password=args.admin_password,
            faculty_password=args.faculty_password,
            student_password=args.student_password,
        )
    finally:
        conn.close()

    print('\n✅ Database reset + seeded successfully')
    print(f"- database: {Config.MYSQL_DATABASE}")
    print('- Admin login: admin@demo.edu / ' + args.admin_password)
    print('- Faculty login: faculty1@demo.edu / ' + args.faculty_password)
    print('- Faculty login: faculty2@demo.edu / ' + args.faculty_password)
    print('- Student login (enrollment): DEMO-CS-0001 / ' + args.student_password)


if __name__ == '__main__':
    main()

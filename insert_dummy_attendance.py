import argparse
import hashlib
from datetime import date, timedelta
from typing import Optional, List, Dict

from db_connection import get_connection, close_connection
from repositories.faculty_repository import FacultyRepository
from repositories.student_repository import StudentRepository
from repositories.timetable_repository import TimetableRepository
from repositories.lecture_repository import LectureRepository
from repositories.attendance_repository import AttendanceRepository


DAY_CODES = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']


def _today_code() -> str:
    return DAY_CODES[date.today().weekday()]


def _pick_default_university_id() -> Optional[int]:
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT university_id FROM universities WHERE is_active = TRUE ORDER BY university_id ASC LIMIT 1"
        )
        row = cursor.fetchone()
        return int(row[0]) if row else None
    finally:
        close_connection(conn)


def _pick_faculty_for_university(university_id: int) -> Optional[Dict]:
    faculty = FacultyRepository.find_all_by_university(university_id)
    if not faculty:
        return None
    # Prefer active
    active = [f for f in faculty if f.get('is_active')]
    return (active[0] if active else faculty[0])


def _ensure_students(university_id: int, min_count: int, password: str) -> List[Dict]:
    existing = StudentRepository.find_all_by_university(university_id)
    if len(existing) >= min_count:
        return existing

    created: List[Dict] = []
    department = 'Computer Science'
    semester = 3

    # Create only the delta
    to_create = min_count - len(existing)
    base_index = len(existing) + 1
    for i in range(base_index, base_index + to_create):
        enrollment_no = f"UNI{university_id}-CS-{i:04d}"
        if StudentRepository.find_by_enrollment(enrollment_no):
            continue

        name = f"Student {i}"
        email = f"student{i}.uni{university_id}@example.com"
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        student_id = StudentRepository.create_student(
            university_id=university_id,
            enrollment_no=enrollment_no,
            name=name,
            department=department,
            semester=semester,
            email=email,
            password_hash=password_hash,
        )

        created.append(
            {
                'student_id': student_id,
                'enrollment_no': enrollment_no,
                'name': name,
                'department': department,
                'semester': semester,
                'email': email,
            }
        )

    return StudentRepository.find_all_by_university(university_id)


def _find_timetable_entry(university_id: int, faculty_id: int, day: str, subject: str, start_time: str, end_time: str) -> Optional[Dict]:
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT * FROM timetable
            WHERE university_id=%s AND faculty_id=%s AND day=%s AND subject=%s AND start_time=%s AND end_time=%s
            LIMIT 1
            """,
            (university_id, faculty_id, day, subject, start_time, end_time),
        )
        return cursor.fetchone()
    finally:
        close_connection(conn)


def _ensure_timetable_for_today(university_id: int, faculty_id: int) -> List[int]:
    day = _today_code()
    department = 'Computer Science'
    semester = 3

    slots = [
        ('Data Structures', '10:00:00', '11:00:00'),
        ('DBMS', '11:00:00', '12:00:00'),
    ]

    timetable_ids: List[int] = []
    for subject, start_time, end_time in slots:
        existing = _find_timetable_entry(university_id, faculty_id, day, subject, start_time, end_time)
        if existing:
            timetable_ids.append(int(existing['timetable_id']))
            continue

        tid = TimetableRepository.create_timetable_entry(
            university_id=university_id,
            faculty_id=faculty_id,
            department=department,
            semester=semester,
            subject=subject,
            day=day,
            start_time=start_time,
            end_time=end_time,
        )
        timetable_ids.append(int(tid))

    return timetable_ids


def _get_lecture_id_if_exists(timetable_id: int, lecture_date: date) -> Optional[int]:
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT lecture_id, status FROM lectures WHERE timetable_id=%s AND lecture_date=%s LIMIT 1",
            (timetable_id, lecture_date),
        )
        row = cursor.fetchone()
        return int(row['lecture_id']) if row else None
    finally:
        close_connection(conn)


def _seed_past_lectures_with_attendance(timetable_id: int, student_ids: List[int], num_lectures: int) -> List[int]:
    created_lecture_ids: List[int] = []

    # Use past dates to avoid conflicting with today's Start Lecture flow.
    offsets = [1, 3, 7, 10, 14]
    offsets = offsets[: max(1, num_lectures)]

    for off in offsets:
        lecture_day = date.today() - timedelta(days=off)
        existing_id = _get_lecture_id_if_exists(timetable_id, lecture_day)
        if existing_id:
            continue

        lecture_id = int(LectureRepository.create_lecture(timetable_id, lecture_day))

        # Mark attendance for a subset of students (cap to 25 for speed)
        subset = student_ids[: min(25, len(student_ids))]
        for idx, sid in enumerate(subset):
            status = 'ABSENT' if (idx % 7 == 0) else 'PRESENT'  # ~14% absent
            try:
                AttendanceRepository.mark_attendance(lecture_id, sid, status)
            except Exception:
                # Ignore duplicates if re-run
                pass

        # End lecture so it shows in history and reports
        try:
            LectureRepository.end_lecture(lecture_id)
        except Exception:
            pass

        created_lecture_ids.append(lecture_id)

    return created_lecture_ids


def main():
    parser = argparse.ArgumentParser(description='Seed timetable/students and some attendance history for testing.')
    parser.add_argument('--university-id', type=int, default=None, help='Target university_id (default: first active university)')
    parser.add_argument('--min-students', type=int, default=15, help='Ensure at least this many students exist')
    parser.add_argument('--student-password', type=str, default='student123', help='Password used for any created students')
    parser.add_argument('--past-lectures', type=int, default=3, help='How many past lectures to create with attendance (per first slot)')
    args = parser.parse_args()

    university_id = args.university_id or _pick_default_university_id()
    if not university_id:
        raise SystemExit('No active university found. Create a university/admin first, then re-run.')

    faculty = _pick_faculty_for_university(university_id)
    if not faculty:
        raise SystemExit('No faculty found. Run insert_dummy_faculty.py first.')

    faculty_id = int(faculty['faculty_id'])
    day = _today_code()

    students = _ensure_students(university_id, args.min_students, args.student_password)
    student_ids = [int(s['student_id']) for s in students]

    timetable_ids = _ensure_timetable_for_today(university_id, faculty_id)

    # Seed a little history using the first timetable slot
    created_lecture_ids: List[int] = []
    if timetable_ids and args.past_lectures > 0:
        created_lecture_ids = _seed_past_lectures_with_attendance(timetable_ids[0], student_ids, args.past_lectures)

    print('\nDummy attendance seed complete')
    print(f'- university_id: {university_id}')
    print(f"- today day code: {day}")
    print(f"- faculty for testing: id={faculty_id}, email={faculty.get('email')}, password=faculty123")
    print(f"- students in university: {len(students)} (created as needed), password for created students: {args.student_password}")
    print(f"- timetable slots ensured for today: {timetable_ids}")
    if created_lecture_ids:
        print(f"- past lecture history created (ENDED): {created_lecture_ids}")


if __name__ == '__main__':
    main()

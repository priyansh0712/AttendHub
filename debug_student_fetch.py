
import mysql.connector
from services.attendance import AttendanceService
from repositories.attendance_repository import AttendanceRepository
from repositories.student_repository import StudentRepository
from repositories.lecture_repository import LectureRepository
from repositories.timetable_repository import TimetableRepository 
from config import Config

# Mock Queue/Set for init
class MockQueue: 
    def enqueue(self, item): pass
    def dequeue(self): return {}

mock_set = set()

def debug_flow():
    print("--- Debugging Start & Mark Flow ---")
    
    # Setup dependencies
    att_repo = AttendanceRepository()
    stud_repo = StudentRepository()
    lec_repo = LectureRepository()
    
    service = AttendanceService(att_repo, stud_repo, lec_repo, MockQueue(), mock_set)
    
    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST, 
        port=Config.MYSQL_PORT, 
        user=Config.MYSQL_USER, 
        password=Config.MYSQL_PASSWORD, 
        database=Config.MYSQL_DATABASE
    )
    cursor = conn.cursor(dictionary=True)

    # 1. Get Faculty & Timetable ID for "Project Demo"
    cursor.execute("SELECT faculty_id FROM faculty WHERE email='faculty@test.com'")
    fac = cursor.fetchone()
    if not fac: 
        print("Faculty not found")
        return
    fid = fac['faculty_id']

    print(f"Faculty ID: {fid}")

    cursor.execute("SELECT timetable_id, subject, semester, department FROM timetable WHERE faculty_id=%s AND subject='Project Demo'", (fid,))
    tt = cursor.fetchone()
    
    if not tt:
        print("Timetable 'Project Demo' not found for this faculty!")
        return
    
    tid = tt['timetable_id']
    print(f"Timetable ID: {tid} ({tt['subject']}, {tt['department']} Sem {tt['semester']})")

    # 2. Check for active/ended lecture
    cursor.execute("SELECT lecture_id, status FROM lectures WHERE timetable_id=%s AND lecture_date=CURDATE()", (tid,))
    lec = cursor.fetchone()
    
    lecture_id = None
    if lec:
        print(f"Found existing lecture: ID {lec['lecture_id']}, Status: {lec['status']}")
        lecture_id = lec['lecture_id']
    else:
        print("No lecture found. Simulating START...")
        # Create one
        lecture_id = LectureRepository.create_lecture(tid, date.today())
        print(f"Created Lecture ID: {lecture_id}")

    # 3. Fetch Students
    print(f"Fetching students for Lecture ID: {lecture_id}...")
    try:
        students = service.get_students_for_lecture(lecture_id)
        print(f"Success! Found {len(students)} students.")
        for s in students:
            print(f" - {s['name']} ({s['enrollment_no']})")
    except Exception as e:
        print(f"ERROR fetching students: {e}")
        import traceback
        traceback.print_exc()

    cursor.close()
    conn.close()

from datetime import date

if __name__ == "__main__":
    try:
        debug_flow()
    except Exception as e:
        print(f"Global Error: {e}")

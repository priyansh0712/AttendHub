from exceptions.custom_exceptions import (
    LectureNotActiveError, 
    AttendanceAlreadyMarkedError, 
    ValidationError,
    RecordNotFoundError
)

class AttendanceService:
    """
    Service to handle attendance marking logic.
    """

    def __init__(self, attendance_repo, student_repo, lecture_repo, queue, attendance_set):
        """
        Constructor with Dependency Injection.
        """
        self.attendance_repo = attendance_repo
        self.student_repo = student_repo
        self.lecture_repo = lecture_repo
        self.request_queue = queue      # Queue for submission requests
        self.attendance_set = attendance_set # Set for in-memory duplicate check (lecture_id, student_id)

    def mark_attendance(self, lecture_id, attendance_list):
        """
        Marks attendance for a list of students for a specific lecture.
        Input: List of { 'student_id': int, 'status': 'PRESENT'|'ABSENT' }
        """
        if not isinstance(attendance_list, list) or not attendance_list:
             # Basic validation, though empty list might be valid if no one showed up? 
             # Let's verify strictness. If empty allow.
             if attendance_list == []: return {"message": "No data to process", "count": 0}
             raise ValidationError("Attendance list must be a list")

        # If any attendance exists for this lecture, do not allow editing/re-marking.
        if self.attendance_repo.attendance_exists_for_lecture(lecture_id):
            raise ValidationError('Attendance already marked for this lecture')

        # 1. Enqueue Request
        self.request_queue.enqueue({
            'lecture_id': lecture_id,
            'students': attendance_list
        })
        
        # 2. Process Request
        req = self.request_queue.dequeue()
        
        # 3. Validation: Check if lecture is active
        lecture = self.lecture_repo.find_by_id(req['lecture_id'])
        if not lecture:
            raise RecordNotFoundError("Lecture not found")
        if lecture['status'] != 'ONGOING':
            raise LectureNotActiveError()

        marked_count = 0
        seen = set()  # per-request duplicate check
        
        # 4. Mark Each Student
        for item in req['students']:
            student_id = item.get('student_id')
            status = item.get('status', 'PRESENT') # Default to PRESENT if missing, though UI should send it

            # Skip duplicates within the same submission payload
            key = (req['lecture_id'], student_id)
            if key in seen:
                continue
            seen.add(key)

            try:
                # Mark in DB
                self.attendance_repo.mark_attendance(req['lecture_id'], student_id, status)
                marked_count += 1
                
            except Exception as e:
                 raise ValidationError(str(e)) from e

        return {"message": "Attendance marked successfully", "count": marked_count}

    def get_today_lectures_with_status(self, faculty_id):
        """Returns today's lectures for the faculty with attendance_marked flag."""
        from datetime import timedelta, time

        def to_time_str(value):
            if value is None:
                return None
            if isinstance(value, timedelta):
                total_seconds = int(value.total_seconds())
                hours = (total_seconds // 3600) % 24
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            if isinstance(value, time):
                return value.strftime('%H:%M:%S')
            return value

        lectures = self.lecture_repo.find_today_lectures_by_faculty(faculty_id) or []
        result = []
        for l in lectures:
            lecture_id = l.get('lecture_id') if isinstance(l, dict) else None
            if not lecture_id:
                continue

            marked = self.attendance_repo.attendance_exists_for_lecture(lecture_id)

            start_time = to_time_str(l.get('start_time')) if isinstance(l, dict) else None
            end_time = to_time_str(l.get('end_time')) if isinstance(l, dict) else None

            result.append({
                'lecture_id': lecture_id,
                'subject': l.get('subject') if isinstance(l, dict) else None,
                'start_time': start_time,
                'end_time': end_time,
                'lecture_status': l.get('status') if isinstance(l, dict) else None,
                'attendance_marked': bool(marked),
            })

        return result

    def get_attendance_by_lecture(self, lecture_id):
        """Retrieves attendance list for a lecture."""
        return self.attendance_repo.find_by_lecture(lecture_id)

    def get_students_for_lecture(self, lecture_id):
        """Returns class-wise students for a given lecture.

        Business rule:
        - Fetch lecture by lecture_id
        - Get timetable_id
        - Fetch timetable details
        - Filter students by timetable.department and timetable.semester
        """
        lecture = self.lecture_repo.find_by_id(lecture_id)
        if not lecture:
            raise RecordNotFoundError("Lecture not found")

        timetable_id = lecture.get('timetable_id')
        if not timetable_id:
            raise ValidationError('Lecture has no timetable_id')

        # TimetableRepository isn't injected into this service currently;
        # import the repository here to keep SQL out of the service.
        from repositories.timetable_repository import TimetableRepository

        timetable = TimetableRepository.find_by_id(timetable_id)
        if not timetable:
            raise RecordNotFoundError('Timetable entry not found')

        department = timetable.get('department')
        semester = timetable.get('semester')
        university_id = timetable.get('university_id')

        if not department or semester is None:
            raise ValidationError('Timetable missing department/semester')

        return self.student_repo.find_by_department_and_semester(
            department=department,
            semester=semester,
            university_id=university_id,
        )

    def get_faculty_attendance_history(self, faculty_id, subject=None, from_date=None, to_date=None):
        """Aggregates lecture history + attendance stats for faculty.

        Optional filters:
        - subject: exact subject match
        - from_date/to_date: YYYY-MM-DD (inclusive)
        """
        lectures = self.lecture_repo.get_faculty_history(
            faculty_id=faculty_id,
            subject=subject,
            from_date=from_date,
            to_date=to_date,
        )
        
        # Enrich with attendance counts
        # (N+1 query problem acceptable for small scale/pagination, optimized in SQL usually)
        result = []
        for l in lectures:
             stats = self.attendance_repo.get_count_summary(l['lecture_id'])
             l['stats'] = stats
             result.append(l)
             
        return result

    def get_student_history(self, student_id):
        """Retrieves attendance history for a student."""
        return self.attendance_repo.find_by_student(student_id)

    def get_student_dashboard_stats(self, student_id):
        """
        Calculates dashboard summary stats: Overall %, Subject count, Alerts.
        """
        history = self.attendance_repo.find_by_student(student_id)
        
        if not history:
             return {
                 'overall_attendance': 0,
                 'subjects_count': 0,
                 'alerts': []
             }
             
        total_lectures = len(history)
        present_count = sum(1 for r in history if r['status'] == 'PRESENT')
        overall_pct = round((present_count / total_lectures * 100), 1) if total_lectures > 0 else 0
        
        # Breakdown by subject
        subjects = {}
        for r in history:
            sub = r['subject']
            if sub not in subjects:
                subjects[sub] = {'total': 0, 'present': 0}
            subjects[sub]['total'] += 1
            if r['status'] == 'PRESENT':
                subjects[sub]['present'] += 1
                
        subjects_count = len(subjects)
        
        # Generate Alerts (e.g. < 75%)
        alerts = []
        for sub, stats in subjects.items():
            pct = (stats['present'] / stats['total']) * 100
            if pct < 75:
                alerts.append({
                    'type': 'warning',
                    'message': f"Low attendance in {sub} ({round(pct)}%)"
                })
                
        return {
            'overall_attendance': overall_pct,
            'subjects_count': subjects_count,
            'alerts': alerts
        }

    def get_student_attendance_summary(self, student_id):
        """Retrieves summary stats for student."""
        history = self.attendance_repo.find_by_student(student_id)
        total = len(history)
        present = sum(1 for record in history if record['status'] == 'PRESENT')
        percentage = (present / total * 100) if total > 0 else 0.0
        return {
            'total_lectures': total,
            'present_count': present,
            'attendance_percentage': round(percentage, 2),
            'history': history # Include full history if needed, or separate
        }

    def get_student_detailed_report(self, student_id):
        """
        Generates detailed subject-wise attendance report for the attendance page.
        """
        history = self.attendance_repo.find_by_student(student_id)
        
        # Overall Stats
        total_lectures = len(history)
        present_count = sum(1 for r in history if r['status'] == 'PRESENT')
        absent_count = total_lectures - present_count
        overall_pct = round((present_count / total_lectures * 100), 1) if total_lectures > 0 else 0
        
        # Subject-wise Stats
        subject_stats = {}
        for r in history:
            sub = r['subject']
            # Assuming subject is just the name for now
            if sub not in subject_stats:
                subject_stats[sub] = {'total': 0, 'present': 0}
            
            subject_stats[sub]['total'] += 1
            if r['status'] == 'PRESENT':
                subject_stats[sub]['present'] += 1
        
        # Format for UI
        subjects_list = []
        for sub, stats in subject_stats.items():
            total = stats['total']
            present = stats['present']
            absent = total - present
            pct = round((present / total * 100), 1) if total > 0 else 0
            
            status_label = "Good"
            if pct < 50:
                status_label = "Critical"
            elif pct < 75:
                status_label = "Warning"
            elif pct < 85:
                 status_label = "Satisfactory"

            subjects_list.append({
                'name': sub,
                'code': '', # Placeholder
                'total': total,
                'present': present,
                'absent': absent,
                'percentage': pct,
                'status': status_label
            })
            
        return {
            'summary': {
                'overallPercentage': overall_pct,
                'totalLectures': total_lectures,
                'totalPresent': present_count,
                'totalAbsent': absent_count
            },
            'subjects': subjects_list
        }

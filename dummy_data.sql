-- Dummy Data Insertion Script
USE aa;

-- 1. Universities
INSERT INTO universities (university_id, university_name, domain, plan, is_active) VALUES 
(1, 'Tech University India', 'techuniv.edu.in', 'PREMIUM', TRUE),
(2, 'Global Institutes', 'globalinst.org', 'FREE', TRUE);

-- 2. Admins
-- Password hash for 'admin123' (SHA256): 240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9
INSERT INTO admins (university_id, name, email, password_hash, is_verified) VALUES 
(1, 'Rajesh Kumar', 'admin@techuniv.edu.in', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', TRUE),
(2, 'Sarah Williams', 'admin@globalinst.org', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', TRUE);

-- 3. Faculty
-- Password hash for 'faculty123' (SHA256): 574efc25e830e0176cdcd0df5f73d82dd8f0b1fe2a392815195dfb8e218228f4
INSERT INTO faculty (university_id, name, email, department, password_hash, is_active) VALUES 
(1, 'Dr. Amit Sharma', 'amit.sharma@techuniv.edu.in', 'Computer Science', '574efc25e830e0176cdcd0df5f73d82dd8f0b1fe2a392815195dfb8e218228f4', TRUE),
(1, 'Prof. Priya Singh', 'priya.singh@techuniv.edu.in', 'Information Technology', '574efc25e830e0176cdcd0df5f73d82dd8f0b1fe2a392815195dfb8e218228f4', TRUE),
(1, 'Dr. Rohan Gupta', 'rohan.gupta@techuniv.edu.in', 'Computer Science', '574efc25e830e0176cdcd0df5f73d82dd8f0b1fe2a392815195dfb8e218228f4', TRUE);

-- 4. Students
-- Password hash for 'student123' (SHA256): a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3
INSERT INTO students (university_id, enrollment_no, name, department, semester, email, password_hash, is_active) VALUES 
(1, 'CS2023001', 'Rahul Verma', 'Computer Science', 6, 'rahul.v@techuniv.edu.in', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', TRUE),
(1, 'CS2023002', 'Sneha Patel', 'Computer Science', 6, 'sneha.p@techuniv.edu.in', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', TRUE),
(1, 'CS2023003', 'Vikram Singh', 'Computer Science', 6, 'vikram.s@techuniv.edu.in', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', TRUE),
(1, 'IT2023001', 'Anjali Das', 'Information Technology', 4, 'anjali.d@techuniv.edu.in', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', TRUE),
(1, 'IT2023002', 'Mohit Kumar', 'Information Technology', 4, 'mohit.k@techuniv.edu.in', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', TRUE);

-- 5. Timetable
-- Monday 10-11 AM for CS Sem 6 by Dr. Amit
INSERT INTO timetable (university_id, faculty_id, department, semester, subject, day, start_time, end_time) VALUES 
(1, 1, 'Computer Science', 6, 'Advanced Algorithms', 'MON', '10:00:00', '11:00:00'),
(1, 1, 'Computer Science', 6, 'Data Structures', 'WED', '14:00:00', '15:00:00'),
(1, 3, 'Computer Science', 6, 'Database Management', 'MON', '11:00:00', '12:00:00'),
(1, 3, 'Computer Science', 6, 'Operating Systems', 'FRI', '09:00:00', '10:00:00'),
(1, 2, 'Information Technology', 4, 'Web Development', 'TUE', '10:00:00', '11:00:00');

-- 6. Lectures
-- Simulate past lectures for dashboard stats
INSERT INTO lectures (timetable_id, lecture_date, status, started_at, ended_at) VALUES 
(1, DATE_SUB(CURDATE(), INTERVAL 7 DAY), 'ENDED', NOW(), NOW()), 
(3, DATE_SUB(CURDATE(), INTERVAL 7 DAY), 'ENDED', NOW(), NOW()),
(1, DATE_SUB(CURDATE(), INTERVAL 2 DAY), 'ENDED', NOW(), NOW());

-- 7. Attendance
-- Mark diverse attendance for the past lectures
-- Lecture 1 (timetable 1)
INSERT INTO attendance (lecture_id, student_id, status) VALUES 
(1, 1, 'PRESENT'), -- Rahul
(1, 2, 'PRESENT'), -- Sneha
(1, 3, 'ABSENT');  -- Vikram

-- Lecture 2 (timetable 3 - same students CS6)
INSERT INTO attendance (lecture_id, student_id, status) VALUES 
(2, 1, 'PRESENT'),
(2, 2, 'ABSENT'),
(2, 3, 'ABSENT');

-- Lecture 3 (timetable 1 again)
INSERT INTO attendance (lecture_id, student_id, status) VALUES 
(3, 1, 'PRESENT'),
(3, 2, 'PRESENT'),
(3, 3, 'PRESENT');
import argparse
from typing import List, Dict, Optional

from db_connection import get_connection, close_connection
from repositories.faculty_repository import FacultyRepository
from services.faculty import FacultyService


def _pick_default_university_id() -> Optional[int]:
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT university_id FROM universities WHERE is_active = TRUE ORDER BY university_id ASC LIMIT 1")
        row = cursor.fetchone()
        return int(row[0]) if row else None
    finally:
        close_connection(conn)


def seed_faculty(university_id: int, count: int, password: str) -> List[Dict]:
    faculty_service = FacultyService(FacultyRepository)

    departments = [
        "Computer Science",
        "Information Technology",
        "Electronics",
        "Mechanical",
        "Civil",
    ]

    created: List[Dict] = []
    for i in range(1, count + 1):
        name = f"Faculty {i}"
        email = f"faculty{i}.uni{university_id}@example.com"
        department = departments[(i - 1) % len(departments)]

        existing = FacultyRepository.find_by_email(email)
        if existing:
            created.append(
                {
                    "status": "exists",
                    "faculty_id": existing.get("faculty_id"),
                    "name": existing.get("name"),
                    "email": existing.get("email"),
                    "department": existing.get("department"),
                    "is_active": bool(existing.get("is_active")),
                }
            )
            continue

        faculty_id = faculty_service.create_faculty(
            university_id=university_id,
            name=name,
            email=email,
            department=department,
            password=password,
        )

        created.append(
            {
                "status": "created",
                "faculty_id": faculty_id,
                "name": name,
                "email": email,
                "department": department,
                "is_active": True,
            }
        )

    return created


def main():
    parser = argparse.ArgumentParser(description="Seed dummy faculty data (idempotent).")
    parser.add_argument("--university-id", type=int, default=None, help="Target university_id (default: first active university)")
    parser.add_argument("--count", type=int, default=8, help="How many faculty to create")
    parser.add_argument("--password", type=str, default="faculty123", help="Password for all created faculty")
    args = parser.parse_args()

    university_id = args.university_id or _pick_default_university_id()
    if not university_id:
        raise SystemExit("No active university found. Create a university/admin first, then re-run.")

    results = seed_faculty(university_id=university_id, count=args.count, password=args.password)

    print(f"\nDummy faculty seed complete for university_id={university_id}")
    print(f"Password for created accounts: {args.password}\n")
    for r in results:
        print(f"- [{r['status']}] id={r['faculty_id']} | {r['name']} | {r['email']} | {r['department']} | active={r['is_active']}")


if __name__ == "__main__":
    main()

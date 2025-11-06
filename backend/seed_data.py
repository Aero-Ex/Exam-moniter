"""
Seed script to populate database with sample data for testing
Run: python seed_data.py
"""

from datetime import datetime, timedelta
from database import SessionLocal, engine, Base
from models import User, Exam, Question, ExamEnrollment, QuestionType, UserRole
from auth import get_password_hash

# Create tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    # Create users
    print("Creating users...")

    # Admin
    admin = User(
        email="admin@example.com",
        username="admin",
        full_name="Admin User",
        hashed_password=get_password_hash("admin123"),
        role=UserRole.ADMIN
    )
    db.add(admin)

    # Teacher
    teacher = User(
        email="teacher@example.com",
        username="teacher",
        full_name="John Teacher",
        hashed_password=get_password_hash("teacher123"),
        role=UserRole.TEACHER
    )
    db.add(teacher)

    # Students
    students = []
    for i in range(1, 6):
        student = User(
            email=f"student{i}@example.com",
            username=f"student{i}",
            full_name=f"Student {i}",
            hashed_password=get_password_hash("student123"),
            role=UserRole.STUDENT
        )
        db.add(student)
        students.append(student)

    db.commit()
    print(f"✓ Created {len(students) + 2} users")

    # Create sample exam
    print("\nCreating sample exam...")

    now = datetime.utcnow()
    exam = Exam(
        title="Python Programming Fundamentals",
        description="Test your knowledge of Python basics including data types, control structures, and functions.",
        duration_minutes=60,
        start_time=now - timedelta(hours=1),  # Started 1 hour ago
        end_time=now + timedelta(hours=2),    # Ends in 2 hours
        creator_id=teacher.id,
        passing_score=60.0,
        proctoring_enabled=True,
        cheating_threshold=10
    )
    db.add(exam)
    db.commit()
    print(f"✓ Created exam: {exam.title}")

    # Create questions
    print("\nCreating questions...")

    questions_data = [
        {
            "question_text": "What is the output of print(type([]))?",
            "question_type": QuestionType.MCQ,
            "points": 1.0,
            "order": 1,
            "options": {
                "A": "<class 'list'>",
                "B": "<class 'dict'>",
                "C": "<class 'tuple'>",
                "D": "<class 'set'>"
            },
            "correct_answer": "A"
        },
        {
            "question_text": "Which of the following is used to define a function in Python?",
            "question_type": QuestionType.MCQ,
            "points": 1.0,
            "order": 2,
            "options": {
                "A": "function",
                "B": "def",
                "C": "func",
                "D": "define"
            },
            "correct_answer": "B"
        },
        {
            "question_text": "What will be the output of: print(2 ** 3)?",
            "question_type": QuestionType.MCQ,
            "points": 1.0,
            "order": 3,
            "options": {
                "A": "5",
                "B": "6",
                "C": "8",
                "D": "9"
            },
            "correct_answer": "C"
        },
        {
            "question_text": "Explain the difference between a list and a tuple in Python.",
            "question_type": QuestionType.SHORT_ANSWER,
            "points": 3.0,
            "order": 4,
            "correct_answer": None
        },
        {
            "question_text": "Write a detailed explanation of how exception handling works in Python. Include examples of try, except, and finally blocks.",
            "question_type": QuestionType.LONG_ANSWER,
            "points": 5.0,
            "order": 5,
            "correct_answer": None
        },
        {
            "question_text": "Write a Python function that takes a list of numbers and returns the sum of all even numbers in the list.",
            "question_type": QuestionType.CODING,
            "points": 5.0,
            "order": 6,
            "test_cases": [
                {"input": "[1, 2, 3, 4, 5, 6]", "expected_output": "12"},
                {"input": "[2, 4, 6, 8]", "expected_output": "20"},
                {"input": "[1, 3, 5, 7]", "expected_output": "0"}
            ],
            "correct_answer": None
        }
    ]

    for q_data in questions_data:
        question = Question(
            exam_id=exam.id,
            **q_data
        )
        db.add(question)

    db.commit()
    print(f"✓ Created {len(questions_data)} questions")

    # Enroll students
    print("\nEnrolling students...")

    for student in students:
        enrollment = ExamEnrollment(
            exam_id=exam.id,
            student_id=student.id
        )
        db.add(enrollment)

    db.commit()
    print(f"✓ Enrolled {len(students)} students")

    # Create another exam (upcoming)
    print("\nCreating upcoming exam...")

    exam2 = Exam(
        title="JavaScript Basics",
        description="Test your understanding of JavaScript fundamentals including variables, functions, and DOM manipulation.",
        duration_minutes=45,
        start_time=now + timedelta(days=2),   # Starts in 2 days
        end_time=now + timedelta(days=2, hours=1),
        creator_id=teacher.id,
        passing_score=70.0,
        proctoring_enabled=True
    )
    db.add(exam2)
    db.commit()
    print(f"✓ Created exam: {exam2.title}")

    # Create past exam
    exam3 = Exam(
        title="Data Structures Quiz",
        description="Completed exam on basic data structures.",
        duration_minutes=30,
        start_time=now - timedelta(days=7),
        end_time=now - timedelta(days=7, hours=-1),
        creator_id=teacher.id,
        passing_score=60.0,
        proctoring_enabled=True
    )
    db.add(exam3)
    db.commit()
    print(f"✓ Created exam: {exam3.title}")

    print("\n" + "="*50)
    print("✓ Database seeded successfully!")
    print("="*50)
    print("\nLogin Credentials:")
    print("-" * 50)
    print("Admin:")
    print("  Username: admin")
    print("  Password: admin123")
    print("\nTeacher:")
    print("  Username: teacher")
    print("  Password: teacher123")
    print("\nStudents:")
    print("  Username: student1, student2, ..., student5")
    print("  Password: student123")
    print("\nActive Exam:")
    print(f"  {exam.title}")
    print(f"  Duration: {exam.duration_minutes} minutes")
    print(f"  Questions: {len(questions_data)}")
    print(f"  Start: {exam.start_time.strftime('%Y-%m-%d %H:%M')}")
    print(f"  End: {exam.end_time.strftime('%Y-%m-%d %H:%M')}")
    print("="*50)

except Exception as e:
    print(f"\n❌ Error seeding database: {e}")
    db.rollback()
finally:
    db.close()

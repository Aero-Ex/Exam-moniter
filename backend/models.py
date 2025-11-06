from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
import enum

class UserRole(str, enum.Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"

class QuestionType(str, enum.Enum):
    MCQ = "mcq"
    SHORT_ANSWER = "short_answer"
    LONG_ANSWER = "long_answer"
    CODING = "coding"

class AlertType(str, enum.Enum):
    LOOKING_AWAY = "looking_away"
    MULTIPLE_PEOPLE = "multiple_people"
    PHONE_DETECTED = "phone_detected"
    READING_FROM_MATERIAL = "reading_from_material"
    TAB_SWITCH = "tab_switch"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.STUDENT)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    exams_created = relationship("Exam", back_populates="creator", foreign_keys="Exam.creator_id")
    exam_sessions = relationship("ExamSession", back_populates="student")
    submissions = relationship("Submission", back_populates="student")

class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    duration_minutes = Column(Integer, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id"))
    passing_score = Column(Float, default=60.0)
    allow_review = Column(Boolean, default=False)
    shuffle_questions = Column(Boolean, default=True)
    proctoring_enabled = Column(Boolean, default=True)
    cheating_threshold = Column(Integer, default=10)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    creator = relationship("User", back_populates="exams_created", foreign_keys=[creator_id])
    questions = relationship("Question", back_populates="exam", cascade="all, delete-orphan")
    exam_sessions = relationship("ExamSession", back_populates="exam")
    enrollments = relationship("ExamEnrollment", back_populates="exam")

class ExamEnrollment(Base):
    __tablename__ = "exam_enrollments"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"))
    student_id = Column(Integer, ForeignKey("users.id"))
    enrolled_at = Column(DateTime, default=datetime.utcnow)

    exam = relationship("Exam", back_populates="enrollments")
    student = relationship("User")

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"))
    question_text = Column(Text, nullable=False)
    question_type = Column(Enum(QuestionType), nullable=False)
    points = Column(Float, default=1.0)
    order = Column(Integer)

    # For MCQ
    options = Column(JSON)  # {"A": "option1", "B": "option2", ...}
    correct_answer = Column(String)  # For MCQ: "A", for others: expected answer or null

    # For coding questions
    test_cases = Column(JSON)  # [{"input": "...", "expected_output": "..."}]

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    exam = relationship("Exam", back_populates="questions")
    answers = relationship("Answer", back_populates="question")

class ExamSession(Base):
    __tablename__ = "exam_sessions"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"))
    student_id = Column(Integer, ForeignKey("users.id"))
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    is_submitted = Column(Boolean, default=False)
    auto_submitted = Column(Boolean, default=False)
    cheating_score = Column(Integer, default=0)
    total_alerts = Column(Integer, default=0)
    video_recording_url = Column(String)
    screen_recording_url = Column(String)

    # Relationships
    exam = relationship("Exam", back_populates="exam_sessions")
    student = relationship("User", back_populates="exam_sessions")
    monitoring_events = relationship("MonitoringEvent", back_populates="session", cascade="all, delete-orphan")
    submission = relationship("Submission", back_populates="session", uselist=False)

class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    answer_text = Column(Text)
    is_correct = Column(Boolean)
    points_earned = Column(Float, default=0.0)

    # Relationships
    submission = relationship("Submission", back_populates="answers")
    question = relationship("Question", back_populates="answers")

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("exam_sessions.id"), unique=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    exam_id = Column(Integer, ForeignKey("exams.id"))
    submitted_at = Column(DateTime, default=datetime.utcnow)
    total_score = Column(Float, default=0.0)
    max_score = Column(Float)
    percentage = Column(Float)
    is_passed = Column(Boolean)
    graded = Column(Boolean, default=False)

    # Relationships
    session = relationship("ExamSession", back_populates="submission")
    student = relationship("User", back_populates="submissions")
    exam = relationship("Exam")
    answers = relationship("Answer", back_populates="submission", cascade="all, delete-orphan")

class MonitoringEvent(Base):
    __tablename__ = "monitoring_events"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("exam_sessions.id"))
    event_type = Column(Enum(AlertType), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    confidence = Column(Float)
    description = Column(Text)
    evidence_url = Column(String)  # URL to screenshot/video clip
    ai_analysis = Column(JSON)  # Raw AI response
    severity = Column(Integer, default=1)  # 1-5

    # Relationships
    session = relationship("ExamSession", back_populates="monitoring_events")

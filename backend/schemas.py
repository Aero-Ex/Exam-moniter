from pydantic import BaseModel, EmailStr, field_serializer
from typing import Optional, List, Dict, Any
from datetime import datetime
from models import UserRole, QuestionType, AlertType

# Helper function to format datetime as UTC ISO string
def serialize_datetime(dt: datetime) -> str:
    """Serialize datetime to ISO format with Z suffix to indicate UTC"""
    if dt is None:
        return None
    # Ensure datetime is treated as UTC
    return dt.isoformat() + 'Z' if not dt.isoformat().endswith('Z') else dt.isoformat()

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    role: UserRole = UserRole.STUDENT

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# Question Schemas
class QuestionBase(BaseModel):
    question_text: str
    question_type: QuestionType
    points: float = 1.0
    order: Optional[int] = None
    options: Optional[Dict[str, str]] = None
    correct_answer: Optional[str] = None
    test_cases: Optional[List[Dict[str, str]]] = None

class QuestionCreate(QuestionBase):
    pass

class QuestionResponse(QuestionBase):
    id: int
    exam_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class QuestionResponseStudent(BaseModel):
    """Question response for students (without correct answers)"""
    id: int
    question_text: str
    question_type: QuestionType
    points: float
    order: Optional[int]
    options: Optional[Dict[str, str]] = None
    exam_id: int

    class Config:
        from_attributes = True

# Exam Schemas
class ExamBase(BaseModel):
    title: str
    description: Optional[str] = None
    duration_minutes: int
    start_time: datetime
    end_time: datetime
    passing_score: float = 60.0
    allow_review: bool = False
    shuffle_questions: bool = True
    proctoring_enabled: bool = True
    cheating_threshold: int = 10

class ExamCreate(ExamBase):
    questions: List[QuestionCreate] = []

class ExamUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    passing_score: Optional[float] = None
    allow_review: Optional[bool] = None
    shuffle_questions: Optional[bool] = None
    proctoring_enabled: Optional[bool] = None
    cheating_threshold: Optional[int] = None

class ExamResponse(ExamBase):
    id: int
    creator_id: int
    created_at: datetime
    questions: List[QuestionResponse] = []

    @field_serializer('start_time', 'end_time', 'created_at')
    def serialize_dt(self, dt: datetime, _info):
        return serialize_datetime(dt)

    class Config:
        from_attributes = True

class ExamResponseStudent(ExamBase):
    id: int
    creator_id: int
    created_at: datetime
    questions: List[QuestionResponseStudent] = []

    @field_serializer('start_time', 'end_time', 'created_at')
    def serialize_dt(self, dt: datetime, _info):
        return serialize_datetime(dt)

    class Config:
        from_attributes = True

class ExamListResponse(ExamBase):
    id: int
    creator_id: int
    created_at: datetime
    total_questions: int

    @field_serializer('start_time', 'end_time', 'created_at')
    def serialize_dt(self, dt: datetime, _info):
        return serialize_datetime(dt)

    class Config:
        from_attributes = True

# Exam Session Schemas
class ExamSessionCreate(BaseModel):
    exam_id: int

class ExamSessionResponse(BaseModel):
    id: int
    exam_id: int
    student_id: int
    start_time: datetime
    end_time: Optional[datetime]
    is_submitted: bool
    auto_submitted: bool
    cheating_score: int
    total_alerts: int
    video_recording_url: Optional[str]
    screen_recording_url: Optional[str]

    class Config:
        from_attributes = True

# Answer Schemas
class AnswerSubmit(BaseModel):
    question_id: int
    answer_text: str

class AnswerResponse(BaseModel):
    id: int
    question_id: int
    answer_text: str
    is_correct: Optional[bool]
    points_earned: float

    class Config:
        from_attributes = True

# Submission Schemas
class SubmissionCreate(BaseModel):
    session_id: int
    answers: List[AnswerSubmit]

class SubmissionResponse(BaseModel):
    id: int
    session_id: int
    student_id: int
    exam_id: int
    submitted_at: datetime
    total_score: float
    max_score: Optional[float]
    percentage: Optional[float]
    is_passed: Optional[bool]
    graded: bool
    answers: List[AnswerResponse] = []

    class Config:
        from_attributes = True

# Monitoring Event Schemas
class MonitoringEventCreate(BaseModel):
    session_id: int
    event_type: AlertType
    confidence: float
    description: str
    evidence_url: Optional[str] = None
    ai_analysis: Optional[Dict[str, Any]] = None
    severity: int = 1

class MonitoringEventResponse(BaseModel):
    id: int
    session_id: int
    event_type: AlertType
    timestamp: datetime
    confidence: float
    description: str
    evidence_url: Optional[str]
    ai_analysis: Optional[Dict[str, Any]]
    severity: int

    class Config:
        from_attributes = True

# AI Analysis Schemas
class FrameAnalysisRequest(BaseModel):
    session_id: int
    image_base64: str
    screen_image_base64: Optional[str] = None

class BehaviorAnalysisReport(BaseModel):
    session_id: int
    total_alerts: int
    alert_breakdown: Dict[str, int]
    timeline: List[MonitoringEventResponse]
    risk_score: float
    summary: str

# Enrollment Schema
class ExamEnrollmentCreate(BaseModel):
    student_ids: List[int]

class ExamEnrollmentResponse(BaseModel):
    id: int
    exam_id: int
    student_id: int
    enrolled_at: datetime

    class Config:
        from_attributes = True

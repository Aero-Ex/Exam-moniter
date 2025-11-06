from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import socketio
import os
from typing import List, Optional

from database import engine, get_db, Base
from models import (
    User, Exam, Question, ExamSession, Answer, Submission,
    MonitoringEvent, ExamEnrollment, UserRole, AlertType
)
from schemas import (
    UserCreate, UserResponse, UserLogin, Token,
    ExamCreate, ExamResponse, ExamUpdate, ExamListResponse, ExamResponseStudent,
    ExamSessionCreate, ExamSessionResponse,
    SubmissionCreate, SubmissionResponse,
    MonitoringEventCreate, MonitoringEventResponse,
    FrameAnalysisRequest, BehaviorAnalysisReport,
    ExamEnrollmentCreate, ExamEnrollmentResponse,
    QuestionResponseStudent
)
from auth import (
    get_password_hash, verify_password, create_access_token,
    get_current_active_user, require_role
)
from ai_service import AIProctorService
from storage_service import StorageService

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI
app = FastAPI(title="Exam Platform API", version="1.0.0")

# CORS configuration
import json
cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
try:
    # Try to parse as JSON array first
    origins = json.loads(cors_origins_str)
except (json.JSONDecodeError, ValueError):
    # Fall back to comma-separated string
    origins = [origin.strip() for origin in cors_origins_str.split(",")]
print(f"Configured CORS origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Socket.IO with proper CORS configuration
# Pass '*' to allow all origins for Socket.IO
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*'
)

socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

# Initialize services
ai_service = AIProctorService()
storage_service = StorageService()

# Store active exam sessions for real-time monitoring
active_sessions = {}  # {session_id: {socket_id, student_id, exam_id}}
# Track ongoing AI analysis to prevent overwhelming the system
ongoing_analysis = {}  # {session_id: timestamp}
# Track good behavior count for positive feedback
good_behavior_count = {}  # {session_id: count}

# ==================== Socket.IO Events ====================

@sio.event
async def connect(sid, environ, auth):
    """Handle socket connection with JWT authentication"""
    try:
        # Extract token from query parameters
        query_string = environ.get("QUERY_STRING", "")
        params = dict(param.split("=") for param in query_string.split("&") if "=" in param)
        token = params.get("token")

        if not token:
            print(f"Connection rejected: No token provided")
            return False

        # Validate token
        from jose import jwt, JWTError
        from auth import SECRET_KEY, ALGORITHM

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            if not user_id:
                print(f"Connection rejected: Invalid token payload")
                return False

            print(f"Client connected: {sid} (User ID: {user_id})")
            return True

        except JWTError as e:
            print(f"Connection rejected: JWT validation failed - {e}")
            return False

    except Exception as e:
        print(f"Connection error: {e}")
        return False

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")
    # Remove from active sessions
    for session_id, data in list(active_sessions.items()):
        if data.get("socket_id") == sid:
            del active_sessions[session_id]

@sio.event
async def join_exam_session(sid, data):
    """Student joins an exam session"""
    session_id = data.get("session_id")
    student_id = data.get("student_id")
    exam_id = data.get("exam_id")

    active_sessions[session_id] = {
        "socket_id": sid,
        "student_id": student_id,
        "exam_id": exam_id
    }

    await sio.emit("session_joined", {"session_id": session_id}, room=sid)
    print(f"Student {student_id} joined exam session {session_id}")

@sio.event
async def join_proctor_room(sid, data):
    """Teacher/admin joins proctor room for an exam"""
    exam_id = data.get("exam_id")
    await sio.enter_room(sid, f"proctor_{exam_id}")
    print(f"Proctor joined room for exam {exam_id}")

@sio.event
async def analyze_frame(sid, data):
    """Analyze webcam/screen frame for cheating detection"""
    try:
        session_id = data.get("session_id")
        webcam_frame = data.get("webcam_frame")  # base64
        screen_frame = data.get("screen_frame")  # base64 (optional)

        # Throttle: Skip if analysis already in progress for this session
        current_time = datetime.utcnow().timestamp()
        if session_id in ongoing_analysis:
            last_analysis_time = ongoing_analysis[session_id]
            # If last analysis was less than 2 seconds ago, skip
            if current_time - last_analysis_time < 2.0:
                return  # Skip this frame to avoid overwhelming the AI

        # Mark analysis as ongoing
        ongoing_analysis[session_id] = current_time

        # Analyze frame with AI
        is_suspicious, analysis = ai_service.analyze_frame(webcam_frame, screen_frame)

        # Clear ongoing flag after analysis
        if session_id in ongoing_analysis:
            del ongoing_analysis[session_id]

        if is_suspicious:
            # Reset good behavior count when violation detected
            good_behavior_count[session_id] = 0
        else:
            # Student is behaving well - send positive feedback periodically
            if session_id not in good_behavior_count:
                good_behavior_count[session_id] = 0

            good_behavior_count[session_id] += 1

            # Send positive feedback every 15 good checks (about every 30 seconds)
            if good_behavior_count[session_id] % 15 == 0:
                student_socket = active_sessions.get(session_id, {}).get("socket_id")
                if student_socket:
                    positive_messages = [
                        "Great job! You're doing well. Keep it up! 👍",
                        "Excellent focus! Keep up the good work! ✨",
                        "Perfect! You're maintaining good exam behavior! ⭐",
                        "Well done! Your focus is impressive! 💯",
                        "Fantastic! Keep maintaining this level of focus! 🎯",
                        "Outstanding! You're following all exam guidelines! 🌟"
                    ]
                    import random
                    message = random.choice(positive_messages)

                    await sio.emit("positive_feedback", {
                        "message": message,
                        "good_behavior_streak": good_behavior_count[session_id]
                    }, room=student_socket)
                    print(f"✅ Positive feedback sent to student {active_sessions[session_id].get('student_id')}: {message}")

        if is_suspicious:
            # Create monitoring event in database
            from database import SessionLocal
            db = SessionLocal()

            try:
                # Upload screenshot to S3
                evidence_url = storage_service.upload_screenshot(
                    webcam_frame,
                    session_id,
                    analysis.get("alert_type", "suspicious_activity")
                )

                # Create event
                alert_type_str = analysis.get("alert_type", "suspicious_activity").upper()
                # Skip if alert type is NONE (no actual violation detected)
                if alert_type_str == "NONE":
                    print(f"[Ollama Debug] Skipping alert with type NONE")
                    return  # Exit without creating event

                event = MonitoringEvent(
                    session_id=session_id,
                    event_type=AlertType[alert_type_str],
                    confidence=analysis.get("confidence", 0.0),
                    description=analysis.get("description", "Suspicious activity detected"),
                    evidence_url=evidence_url,
                    ai_analysis=analysis,
                    severity=analysis.get("severity", 3)
                )
                db.add(event)

                # Update session cheating score
                session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
                if session:
                    session.cheating_score += analysis.get("severity", 1)
                    session.total_alerts += 1

                    # Send warning to student
                    student_socket = active_sessions.get(session_id, {}).get("socket_id")
                    if student_socket:
                        await sio.emit("cheating_warning", {
                            "description": analysis.get("description", "Suspicious activity detected"),
                            "alert_type": analysis.get("alert_type"),
                            "severity": analysis.get("severity"),
                            "warning_count": session.total_alerts,
                            "cheating_score": session.cheating_score,
                            "threshold": exam.cheating_threshold if 'exam' in locals() else 10
                        }, room=student_socket)
                        print(f"⚠️  Warning sent to student {session.student_id}: {analysis.get('description')}")

                    # Check if threshold exceeded
                    exam = db.query(Exam).filter(Exam.id == session.exam_id).first()
                    if session.cheating_score >= exam.cheating_threshold and not session.is_submitted:
                        # Auto-submit exam
                        session.is_submitted = True
                        session.auto_submitted = True
                        session.end_time = datetime.utcnow()

                        # Notify student
                        student_socket = active_sessions.get(session_id, {}).get("socket_id")
                        if student_socket:
                            await sio.emit("exam_auto_submitted", {
                                "reason": "Cheating threshold exceeded",
                                "cheating_score": session.cheating_score
                            }, room=student_socket)

                db.commit()

                # Notify proctors
                await sio.emit("cheating_alert", {
                    "session_id": session_id,
                    "student_id": session.student_id,
                    "event_type": analysis.get("alert_type"),
                    "description": analysis.get("description"),
                    "confidence": analysis.get("confidence"),
                    "severity": analysis.get("severity"),
                    "timestamp": datetime.utcnow().isoformat(),
                    "evidence_url": evidence_url
                }, room=f"proctor_{session.exam_id}")

            finally:
                db.close()

    except Exception as e:
        print(f"Error analyzing frame: {e}")
        # Clear ongoing flag even on error
        if session_id in ongoing_analysis:
            del ongoing_analysis[session_id]

@sio.event
async def tab_switch_detected(sid, data):
    """Handle tab switch detection from client"""
    session_id = data.get("session_id")

    from database import SessionLocal
    db = SessionLocal()

    try:
        event = MonitoringEvent(
            session_id=session_id,
            event_type=AlertType.TAB_SWITCH,
            confidence=1.0,
            description="Student switched browser tab or window",
            severity=2
        )
        db.add(event)

        # Update session
        session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
        if session:
            session.cheating_score += 2
            session.total_alerts += 1

            # Send warning to student
            student_socket = active_sessions.get(session_id, {}).get("socket_id")
            if student_socket:
                await sio.emit("cheating_warning", {
                    "description": "Tab switching detected! Stay focused on the exam.",
                    "alert_type": "tab_switch",
                    "severity": 2,
                    "warning_count": session.total_alerts,
                    "cheating_score": session.cheating_score
                }, room=student_socket)
                print(f"⚠️  Tab switch warning sent to student {session.student_id}")

        db.commit()

        # Notify proctors
        await sio.emit("cheating_alert", {
            "session_id": session_id,
            "student_id": session.student_id,
            "event_type": "tab_switch",
            "description": "Browser tab/window switch detected",
            "severity": 2,
            "timestamp": datetime.utcnow().isoformat()
        }, room=f"proctor_{session.exam_id}")

    finally:
        db.close()

# ==================== Authentication Routes ====================

@app.post("/api/auth/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user exists
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    # Create user
    db_user = User(
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        hashed_password=get_password_hash(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

@app.post("/api/auth/login", response_model=Token)
def login(form_data: UserLogin, db: Session = Depends(get_db)):
    """Login user and return JWT token"""
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="User account is inactive")

    access_token = create_access_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@app.get("/api/auth/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user

# ==================== Exam Routes ====================

@app.post("/api/exams", response_model=ExamResponse)
def create_exam(
    exam: ExamCreate,
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Create a new exam (Teacher/Admin only)"""
    db_exam = Exam(
        title=exam.title,
        description=exam.description,
        duration_minutes=exam.duration_minutes,
        start_time=exam.start_time,
        end_time=exam.end_time,
        creator_id=current_user.id,
        passing_score=exam.passing_score,
        allow_review=exam.allow_review,
        shuffle_questions=exam.shuffle_questions,
        proctoring_enabled=exam.proctoring_enabled,
        cheating_threshold=exam.cheating_threshold
    )
    db.add(db_exam)
    db.commit()
    db.refresh(db_exam)

    # Add questions
    for i, q in enumerate(exam.questions):
        question = Question(
            exam_id=db_exam.id,
            question_text=q.question_text,
            question_type=q.question_type,
            points=q.points,
            order=q.order if q.order is not None else i,
            options=q.options,
            correct_answer=q.correct_answer,
            test_cases=q.test_cases
        )
        db.add(question)

    db.commit()
    db.refresh(db_exam)

    return db_exam

@app.get("/api/exams", response_model=List[ExamListResponse])
def list_exams(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all exams"""
    if current_user.role in [UserRole.TEACHER, UserRole.ADMIN]:
        # Teachers/Admins see all exams
        exams = db.query(Exam).all()
    else:
        # Students see only enrolled exams
        enrollments = db.query(ExamEnrollment).filter(
            ExamEnrollment.student_id == current_user.id
        ).all()
        exam_ids = [e.exam_id for e in enrollments]
        exams = db.query(Exam).filter(Exam.id.in_(exam_ids)).all()

    # Add question count
    result = []
    for exam in exams:
        exam_dict = {
            **exam.__dict__,
            "total_questions": len(exam.questions)
        }
        result.append(exam_dict)

    return result

@app.get("/api/exams/{exam_id}")
def get_exam(
    exam_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get exam details"""
    from sqlalchemy.orm import joinedload

    # Eagerly load questions to avoid lazy loading issues
    exam = db.query(Exam).options(joinedload(Exam.questions)).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # Check access
    if current_user.role == UserRole.STUDENT:
        # Check if student is enrolled
        enrollment = db.query(ExamEnrollment).filter(
            ExamEnrollment.exam_id == exam_id,
            ExamEnrollment.student_id == current_user.id
        ).first()
        if not enrollment:
            raise HTTPException(status_code=403, detail="Not enrolled in this exam")

        # Return without correct answers for students
        return ExamResponseStudent.model_validate(exam)

    return ExamResponse.model_validate(exam)

@app.put("/api/exams/{exam_id}", response_model=ExamResponse)
def update_exam(
    exam_id: int,
    exam_update: ExamUpdate,
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Update an exam"""
    db_exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not db_exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # Update fields
    for field, value in exam_update.dict(exclude_unset=True).items():
        setattr(db_exam, field, value)

    db.commit()
    db.refresh(db_exam)

    return db_exam

@app.delete("/api/exams/{exam_id}")
def delete_exam(
    exam_id: int,
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Delete an exam"""
    db_exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not db_exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    db.delete(db_exam)
    db.commit()

    return {"message": "Exam deleted successfully"}

# ==================== Exam Enrollment Routes ====================

@app.post("/api/exams/{exam_id}/enroll", response_model=List[ExamEnrollmentResponse])
def enroll_students(
    exam_id: int,
    enrollment: ExamEnrollmentCreate,
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Enroll students in an exam"""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    enrollments = []
    for student_id in enrollment.student_ids:
        # Check if already enrolled
        existing = db.query(ExamEnrollment).filter(
            ExamEnrollment.exam_id == exam_id,
            ExamEnrollment.student_id == student_id
        ).first()

        if not existing:
            enroll = ExamEnrollment(exam_id=exam_id, student_id=student_id)
            db.add(enroll)
            enrollments.append(enroll)

    db.commit()

    return enrollments

# ==================== Exam Session Routes ====================

@app.post("/api/sessions/start", response_model=ExamSessionResponse)
def start_exam_session(
    session_data: ExamSessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Start an exam session"""
    # Check if exam exists and student is enrolled
    exam = db.query(Exam).filter(Exam.id == session_data.exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    enrollment = db.query(ExamEnrollment).filter(
        ExamEnrollment.exam_id == session_data.exam_id,
        ExamEnrollment.student_id == current_user.id
    ).first()
    if not enrollment:
        raise HTTPException(status_code=403, detail="Not enrolled in this exam")

    # Check if exam is currently active
    now = datetime.utcnow()
    if now < exam.start_time:
        raise HTTPException(status_code=400, detail="Exam has not started yet")
    if now > exam.end_time:
        raise HTTPException(status_code=400, detail="Exam has ended")

    # Check if student already has an active session
    existing_session = db.query(ExamSession).filter(
        ExamSession.exam_id == session_data.exam_id,
        ExamSession.student_id == current_user.id,
        ExamSession.is_submitted == False
    ).first()

    if existing_session:
        return existing_session

    # Create new session
    session = ExamSession(
        exam_id=session_data.exam_id,
        student_id=current_user.id,
        start_time=datetime.utcnow()
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return session

@app.get("/api/sessions/{session_id}", response_model=ExamSessionResponse)
def get_exam_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get exam session details"""
    session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check access
    if current_user.role == UserRole.STUDENT and session.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return session

# ==================== Submission Routes ====================

@app.post("/api/submissions", response_model=SubmissionResponse)
def submit_exam(
    submission_data: SubmissionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Submit exam answers"""
    # Get session
    session = db.query(ExamSession).filter(ExamSession.id == submission_data.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if session.is_submitted:
        # Check if submission already exists
        existing_submission = db.query(Submission).filter(
            Submission.session_id == session.id
        ).first()
        if existing_submission:
            return existing_submission
        raise HTTPException(status_code=400, detail="Exam already submitted")

    # Check if submission already exists for this session
    existing_submission = db.query(Submission).filter(
        Submission.session_id == session.id
    ).first()
    if existing_submission:
        return existing_submission

    # Create submission
    submission = Submission(
        session_id=session.id,
        student_id=current_user.id,
        exam_id=session.exam_id
    )
    db.add(submission)
    db.flush()

    # Process answers and calculate score
    total_score = 0.0
    max_score = 0.0

    exam = db.query(Exam).filter(Exam.id == session.exam_id).first()

    for answer_data in submission_data.answers:
        question = db.query(Question).filter(Question.id == answer_data.question_id).first()
        if not question:
            continue

        max_score += question.points

        # Grade answer
        is_correct = False
        points_earned = 0.0

        if question.question_type.value == "mcq":
            if answer_data.answer_text.strip().upper() == question.correct_answer.strip().upper():
                is_correct = True
                points_earned = question.points

        # For other types, teacher needs to grade manually
        # Coding questions can be auto-graded if test cases are provided

        answer = Answer(
            submission_id=submission.id,
            question_id=question.id,
            answer_text=answer_data.answer_text,
            is_correct=is_correct,
            points_earned=points_earned
        )
        db.add(answer)

        total_score += points_earned

    # Update submission
    submission.total_score = total_score
    submission.max_score = max_score
    submission.percentage = (total_score / max_score * 100) if max_score > 0 else 0
    submission.is_passed = submission.percentage >= exam.passing_score
    submission.graded = True  # Set to False if manual grading needed

    # Update session
    session.is_submitted = True
    session.end_time = datetime.utcnow()

    db.commit()
    db.refresh(submission)

    return submission

@app.get("/api/submissions/{submission_id}", response_model=SubmissionResponse)
def get_submission(
    submission_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get submission details"""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    # Check access
    if current_user.role == UserRole.STUDENT and submission.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return submission

# ==================== Monitoring Routes ====================

@app.get("/api/sessions/{session_id}/events", response_model=List[MonitoringEventResponse])
def get_monitoring_events(
    session_id: int,
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get all monitoring events for a session"""
    events = db.query(MonitoringEvent).filter(
        MonitoringEvent.session_id == session_id
    ).order_by(MonitoringEvent.timestamp.desc()).all()

    return events

@app.get("/api/sessions/{session_id}/behavior-report", response_model=BehaviorAnalysisReport)
def get_behavior_report(
    session_id: int,
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Generate behavioral analysis report for a session"""
    session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    events = db.query(MonitoringEvent).filter(
        MonitoringEvent.session_id == session_id
    ).order_by(MonitoringEvent.timestamp.asc()).all()

    report = ai_service.generate_behavior_report(events)

    return {
        "session_id": session_id,
        "timeline": events,
        **report
    }

# ==================== Admin/Teacher Dashboard Routes ====================

@app.get("/api/admin/students", response_model=List[UserResponse])
def list_students(
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """List all students"""
    students = db.query(User).filter(User.role == UserRole.STUDENT).all()
    return students

@app.get("/api/admin/exams/{exam_id}/sessions", response_model=List[ExamSessionResponse])
def get_exam_sessions(
    exam_id: int,
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get all sessions for an exam (for proctoring dashboard)"""
    sessions = db.query(ExamSession).filter(ExamSession.exam_id == exam_id).all()
    return sessions

@app.get("/api/admin/live-sessions")
def get_live_sessions(
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN]))
):
    """Get currently active exam sessions"""
    return {
        "active_sessions": [
            {
                "session_id": session_id,
                "student_id": data["student_id"],
                "exam_id": data["exam_id"]
            }
            for session_id, data in active_sessions.items()
        ]
    }

# ==================== Health Check ====================

@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "exam-platform-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(socket_app, host="0.0.0.0", port=8000)

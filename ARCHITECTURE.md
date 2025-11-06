# System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Student    │  │   Teacher    │  │    Admin     │          │
│  │  Dashboard   │  │  Dashboard   │  │   Panel      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                  │                  │                  │
│         └──────────────────┴──────────────────┘                  │
│                          │                                       │
│                          ▼                                       │
│              ┌─────────────────────┐                            │
│              │   React Frontend    │                            │
│              │  (TypeScript, Vite) │                            │
│              └─────────────────────┘                            │
│                     │         │                                 │
│              ┌──────┴─────┐   └────────┐                        │
│              │            │            │                        │
└──────────────┼────────────┼────────────┼────────────────────────┘
               │            │            │
               │ HTTP/REST  │ WebSocket  │ WebRTC
               │            │            │
┌──────────────┼────────────┼────────────┼────────────────────────┐
│              │            │            │                        │
│              ▼            ▼            ▼                        │
│         ┌──────────────────────────────────┐                   │
│         │      FastAPI Backend             │                   │
│         │                                  │                   │
│         │  ┌─────────────────────────┐    │                   │
│         │  │  REST API Endpoints     │    │                   │
│         │  └─────────────────────────┘    │                   │
│         │  ┌─────────────────────────┐    │                   │
│         │  │  Socket.IO Server       │    │                   │
│         │  └─────────────────────────┘    │                   │
│         │  ┌─────────────────────────┐    │                   │
│         │  │  Authentication (JWT)   │    │                   │
│         │  └─────────────────────────┘    │                   │
│         └──────────────────────────────────┘                   │
│                     │         │                                │
│              ┌──────┴─────┐   └────────┐                       │
│              │            │            │                       │
│              ▼            ▼            ▼                       │
├─────────────────────────────────────────────────────────────────┤
│                      SERVICE LAYER                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐ │
│  │   AI Proctoring │  │  Storage Service│  │  Auth Service  │ │
│  │    Service      │  │   (AWS S3)      │  │     (JWT)      │ │
│  └─────────────────┘  └─────────────────┘  └────────────────┘ │
│          │                     │                               │
│          ▼                     ▼                               │
│  ┌─────────────────┐  ┌─────────────────┐                     │
│  │  OpenAI GPT-4   │  │   AWS S3        │                     │
│  │  Vision API     │  │   Bucket        │                     │
│  │  (or Qwen3-VL)  │  │                 │                     │
│  └─────────────────┘  └─────────────────┘                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                       DATA LAYER                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│              ┌─────────────────────────┐                        │
│              │   PostgreSQL Database   │                        │
│              │                         │                        │
│              │  ┌───────────────────┐  │                        │
│              │  │ Users             │  │                        │
│              │  │ Exams             │  │                        │
│              │  │ Questions         │  │                        │
│              │  │ Exam Sessions     │  │                        │
│              │  │ Submissions       │  │                        │
│              │  │ Monitoring Events │  │                        │
│              │  └───────────────────┘  │                        │
│              └─────────────────────────┘                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### Frontend Components

```
src/
├── pages/
│   ├── Login.tsx              # Authentication page
│   ├── Dashboard.tsx          # Main dashboard
│   ├── TakeExam.tsx          # Exam taking interface
│   └── AdminPanel.tsx        # Proctoring dashboard
│
├── components/
│   └── ui/
│       ├── Button.tsx        # Reusable button
│       ├── Input.tsx         # Form input
│       └── Card.tsx          # Card container
│
├── lib/
│   ├── api.ts               # HTTP client
│   ├── socket.ts            # WebSocket client
│   └── utils.ts             # Helper functions
│
└── store/
    ├── authStore.ts         # Auth state
    └── themeStore.ts        # Theme state
```

### Backend Components

```
backend/
├── main.py                  # FastAPI app + routes
├── database.py              # DB configuration
├── models.py                # Database models
├── schemas.py               # Pydantic schemas
├── auth.py                  # Authentication logic
├── ai_service.py            # AI proctoring
└── storage_service.py       # S3 storage
```

## Data Flow

### 1. Exam Taking Flow

```
Student Opens Exam
       │
       ▼
Request Camera Permission
       │
       ▼
Start Exam Session (POST /api/sessions/start)
       │
       ▼
Join Socket.IO Room (join_exam_session)
       │
       ▼
┌──────────────────────────────────┐
│  Continuous Monitoring Loop      │
│                                  │
│  Every 5 seconds:                │
│  1. Capture webcam frame         │
│  2. Send to backend via Socket   │
│  3. AI analyzes frame            │
│  4. Generate alert if suspicious │
│  5. Update cheating score        │
└──────────────────────────────────┘
       │
       ▼
Student Submits Answers
       │
       ▼
POST /api/submissions
       │
       ▼
Auto-grade MCQ Questions
       │
       ▼
Store Results in Database
       │
       ▼
Return to Dashboard
```

### 2. AI Analysis Flow

```
Webcam Frame Captured
       │
       ▼
Send to Backend via Socket.IO (analyze_frame)
       │
       ▼
AI Service Receives Frame
       │
       ▼
┌────────────────────────────┐
│  Send to AI Model:         │
│  - OpenAI GPT-4 Vision     │
│    OR                      │
│  - Qwen3-VL               │
└────────────────────────────┘
       │
       ▼
AI Returns Analysis:
- is_suspicious: true/false
- confidence: 0.0-1.0
- detected_issues: []
- alert_type: string
- description: string
       │
       ▼
If Suspicious (confidence >= threshold):
       │
       ├─ Upload screenshot to S3
       ├─ Create MonitoringEvent in DB
       ├─ Update session cheating_score
       └─ Emit alert to proctor (Socket.IO)
       │
       ▼
If cheating_score >= threshold:
       │
       └─ Auto-submit exam
```

### 3. Real-Time Proctoring Flow

```
Teacher Opens Proctoring Dashboard
       │
       ▼
Load Active Sessions (GET /api/admin/exams/{id}/sessions)
       │
       ▼
Join Proctor Room (join_proctor_room)
       │
       ▼
Listen for Real-Time Events:
       │
       ├─ cheating_alert (when student does something suspicious)
       ├─ tab_switch_detected
       └─ exam_auto_submitted
       │
       ▼
Display Alerts in Real-Time
       │
       ▼
Teacher Can:
- View live camera feeds
- See alert timeline
- Check cheating scores
- Generate behavior reports
- Review evidence screenshots
```

## Security Layers

```
┌─────────────────────────────────────┐
│        Application Security         │
│                                     │
│  ┌───────────────────────────────┐ │
│  │ Input Validation (Pydantic)   │ │
│  └───────────────────────────────┘ │
│  ┌───────────────────────────────┐ │
│  │ SQL Injection Prevention      │ │
│  │ (SQLAlchemy ORM)             │ │
│  └───────────────────────────────┘ │
│  ┌───────────────────────────────┐ │
│  │ XSS Protection                │ │
│  └───────────────────────────────┘ │
└─────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│      Authentication Security        │
│                                     │
│  ┌───────────────────────────────┐ │
│  │ Password Hashing (bcrypt)     │ │
│  └───────────────────────────────┘ │
│  ┌───────────────────────────────┐ │
│  │ JWT Token Authentication      │ │
│  └───────────────────────────────┘ │
│  ┌───────────────────────────────┐ │
│  │ Role-Based Access Control     │ │
│  └───────────────────────────────┘ │
└─────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│       Exam Security                 │
│                                     │
│  ┌───────────────────────────────┐ │
│  │ Fullscreen Enforcement        │ │
│  └───────────────────────────────┘ │
│  ┌───────────────────────────────┐ │
│  │ Copy/Paste Prevention         │ │
│  └───────────────────────────────┘ │
│  ┌───────────────────────────────┐ │
│  │ Tab Switch Detection          │ │
│  └───────────────────────────────┘ │
│  ┌───────────────────────────────┐ │
│  │ Keyboard Shortcut Blocking    │ │
│  └───────────────────────────────┘ │
└─────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│       Network Security              │
│                                     │
│  ┌───────────────────────────────┐ │
│  │ CORS Protection               │ │
│  └───────────────────────────────┘ │
│  ┌───────────────────────────────┐ │
│  │ HTTPS/TLS (Production)        │ │
│  └───────────────────────────────┘ │
└─────────────────────────────────────┘
```

## Database Schema

```
┌─────────────┐       ┌──────────────┐       ┌─────────────┐
│    Users    │       │    Exams     │       │  Questions  │
├─────────────┤       ├──────────────┤       ├─────────────┤
│ id          │       │ id           │◄──────│ id          │
│ email       │       │ title        │       │ exam_id     │
│ username    │       │ description  │       │ question_   │
│ password    │       │ duration     │       │   text      │
│ full_name   │       │ start_time   │       │ type        │
│ role        │       │ end_time     │       │ points      │
│ is_active   │       │ creator_id   │       │ options     │
└─────────────┘       └──────────────┘       │ correct_    │
       │                      │               │   answer    │
       │                      │               └─────────────┘
       │                      │
       │              ┌───────┴────────┐
       │              │                │
       ▼              ▼                ▼
┌─────────────┐  ┌──────────────┐  ┌────────────────┐
│Exam Sessions│  │ Enrollments  │  │  Submissions   │
├─────────────┤  ├──────────────┤  ├────────────────┤
│ id          │  │ id           │  │ id             │
│ exam_id     │  │ exam_id      │  │ session_id     │
│ student_id  │  │ student_id   │  │ student_id     │
│ start_time  │  │ enrolled_at  │  │ exam_id        │
│ end_time    │  └──────────────┘  │ submitted_at   │
│ is_submitted│                    │ total_score    │
│ cheating_   │                    │ max_score      │
│   score     │                    │ percentage     │
│ total_      │                    │ is_passed      │
│   alerts    │                    └────────────────┘
└─────────────┘                            │
       │                                   │
       │                                   ▼
       │                          ┌─────────────┐
       │                          │   Answers   │
       │                          ├─────────────┤
       │                          │ id          │
       │                          │ submission_ │
       │                          │   id        │
       │                          │ question_id │
       │                          │ answer_text │
       │                          │ is_correct  │
       │                          │ points_     │
       │                          │   earned    │
       │                          └─────────────┘
       │
       ▼
┌─────────────────┐
│Monitoring Events│
├─────────────────┤
│ id              │
│ session_id      │
│ event_type      │
│ timestamp       │
│ confidence      │
│ description     │
│ evidence_url    │
│ ai_analysis     │
│ severity        │
└─────────────────┘
```

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Load Balancer                       │
│                    (Nginx/CloudFlare)                    │
└────────────────┬─────────────────────┬──────────────────┘
                 │                     │
       ┌─────────┴─────────┐  ┌───────┴────────┐
       │                   │  │                │
       ▼                   ▼  ▼                ▼
┌─────────────┐     ┌─────────────┐    ┌─────────────┐
│  Frontend   │     │  Backend    │    │  Backend    │
│  (Static)   │     │  Instance 1 │    │  Instance 2 │
│   CDN       │     │  (FastAPI)  │    │  (FastAPI)  │
└─────────────┘     └─────────────┘    └─────────────┘
                           │                  │
                           └────────┬─────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
            ┌────────────┐  ┌────────────┐  ┌────────────┐
            │ PostgreSQL │  │   Redis    │  │  AWS S3    │
            │  (Primary) │  │  (Cache)   │  │  (Videos)  │
            └────────────┘  └────────────┘  └────────────┘
                    │
                    ▼
            ┌────────────┐
            │ PostgreSQL │
            │  (Replica) │
            └────────────┘
```

## Technologies Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | React 18 | UI Framework |
| Frontend | TypeScript | Type Safety |
| Frontend | Tailwind CSS | Styling |
| Frontend | Vite | Build Tool |
| Frontend | Socket.IO | Real-time |
| Backend | FastAPI | API Framework |
| Backend | Python 3.9+ | Language |
| Backend | SQLAlchemy | ORM |
| Backend | Socket.IO | WebSocket |
| Database | PostgreSQL | Data Storage |
| AI | OpenAI GPT-4 Vision | Proctoring |
| AI | Qwen3-VL | Alternative |
| Storage | AWS S3 | File Storage |
| Auth | JWT | Authentication |
| Server | Uvicorn | ASGI Server |

This architecture provides:
- ✅ Scalability
- ✅ High availability
- ✅ Real-time capabilities
- ✅ Security
- ✅ Maintainability
- ✅ Performance

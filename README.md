# Online Examination Platform with AI-Powered Proctoring

A full-featured online examination platform with advanced AI-based anti-cheating detection using computer vision and behavioral analysis.

## Features

### Student Features
- 🔐 Secure login and authentication
- 📝 Multiple question types (MCQ, Short Answer, Long Answer, Coding)
- 📹 Real-time webcam monitoring
- 🖥️ Screen activity tracking
- ⏱️ Auto-save and timed exams
- 🎯 Instant results for auto-graded questions
- 📊 Performance analytics

### AI-Powered Anti-Cheating
- 👁️ **Looking away detection** - Detects when student looks away from screen
- 👥 **Multiple people detection** - Identifies additional people in frame
- 📱 **Phone/device detection** - Detects use of unauthorized devices
- 📚 **Reading material detection** - Identifies books, notes, or papers
- 🖱️ **Tab switching detection** - Monitors browser focus changes
- 🤖 **AI behavioral analysis** - Comprehensive cheating risk assessment

### Admin/Teacher Features
- 📋 Exam creation and management
- 👨‍🎓 Student enrollment
- 📺 Live proctoring dashboard
- 🚨 Real-time alert notifications
- 📊 Behavioral analysis reports
- 📈 Results analytics
- 🎥 Video recording playback

### Security Features
- 🔒 Secure browser mode (prevents tab switching, copy/paste)
- 🚫 Disabled right-click, keyboard shortcuts, print screen
- 🖥️ Fullscreen enforcement
- 📹 Continuous video recording
- ⚠️ Auto-submission on cheating threshold breach
- 🔐 JWT authentication

### UI Features
- 🌓 Light/Dark mode
- 📱 Responsive design
- ⚡ Real-time updates via WebSocket
- 🎨 Modern, clean interface
- ♿ Accessible components

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Relational database
- **SQLAlchemy** - ORM
- **Socket.IO** - Real-time communication
- **Ollama + Qwen3-VL 8B** - Local AI proctoring (recommended)
- **OpenAI GPT-4 Vision** - Alternative cloud AI (optional)
- **AWS S3** - Video/screenshot storage (optional)
- **JWT** - Authentication

### Frontend
- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Socket.IO Client** - Real-time updates
- **React Query** - Data fetching
- **Zustand** - State management
- **React Webcam** - Camera access

## Installation

### Prerequisites

**Required:**
- Python 3.9+
- Node.js 18+
- PostgreSQL 14+
- **Ollama** with Qwen3-VL model (recommended - see [OLLAMA_SETUP.md](OLLAMA_SETUP.md))

**Optional:**
- OpenAI API key (alternative to Ollama)
- AWS S3 bucket (for evidence storage - platform works without it)

### Backend Setup

1. Navigate to backend directory:
```bash
cd exam-platform/backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Set up database:
```bash
# Create PostgreSQL database
createdb exam_platform

# Update DATABASE_URL in .env
DATABASE_URL=postgresql://user:password@localhost:5432/exam_platform
```

6. Run the server:
```bash
python main.py
# Or with uvicorn:
uvicorn main:socket_app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd exam-platform/frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start development server:
```bash
npm run dev
```

4. Open browser at `http://localhost:5173`

## Configuration

### Environment Variables

#### Backend (.env)

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/exam_platform

# JWT
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Proctoring - LOCAL OLLAMA (Default & Recommended!)
USE_OLLAMA=true
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen3-vl:8b

# Alternative: OpenAI (Cloud API)
# USE_OLLAMA=false
# OPENAI_API_KEY=sk-your-openai-api-key

# AWS S3 (OPTIONAL - for evidence storage)
# AWS_ACCESS_KEY_ID=your-aws-access-key
# AWS_SECRET_ACCESS_KEY=your-aws-secret-key
# AWS_REGION=us-east-1
# S3_BUCKET_NAME=exam-platform-recordings

# Thresholds
CHEATING_THRESHOLD_AUTO_SUBMIT=10
ALERT_CONFIDENCE_THRESHOLD=0.6

# CORS
CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]
```

### AI Proctoring Setup

#### Option 1: Ollama (Recommended - Free & Private)

**Advantages:**
- ✅ Completely free - no API costs
- ✅ 100% private - all processing done locally
- ✅ Works offline
- ✅ Fast inference
- ✅ No API keys required

**Setup:**
```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull Qwen3-VL model
ollama pull qwen3-vl:8b

# 3. Start Ollama (if not running)
ollama serve
```

See [OLLAMA_SETUP.md](OLLAMA_SETUP.md) for detailed instructions.

#### Option 2: OpenAI GPT-4 Vision (Cloud Alternative)

If you prefer cloud-based AI:

1. Set `USE_OLLAMA=false` in .env
2. Add your OpenAI API key: `OPENAI_API_KEY=sk-...`
3. Note: This will incur API costs (~$0.01 per image)

## Usage

### For Students

1. **Login**: Navigate to login page and enter credentials
2. **View Exams**: See available exams on dashboard
3. **Take Exam**:
   - Click "Take Exam" button
   - Grant camera permissions
   - Read instructions carefully
   - Start exam (will enter fullscreen mode)
   - Answer questions
   - Submit when complete

### For Teachers/Admins

1. **Create Exam**:
   - Navigate to "Create Exam" page
   - Fill in exam details
   - Add questions
   - Set proctoring settings
   - Publish exam

2. **Enroll Students**:
   - Open exam details
   - Click "Enroll Students"
   - Select students to enroll

3. **Monitor Exams**:
   - Go to "Live Proctoring" dashboard
   - View active exam sessions
   - See real-time alerts
   - Watch live camera feeds
   - Review behavioral analysis

4. **Grade Exams**:
   - MCQ questions are auto-graded
   - Manually grade essay/coding questions
   - Review proctoring reports

## API Documentation

Once the backend is running, visit:
- API Docs: `http://localhost:8000/docs`
- Alternative Docs: `http://localhost:8000/redoc`

### Key Endpoints

#### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user

#### Exams
- `GET /api/exams` - List exams
- `POST /api/exams` - Create exam (Teacher/Admin)
- `GET /api/exams/{id}` - Get exam details
- `PUT /api/exams/{id}` - Update exam (Teacher/Admin)
- `DELETE /api/exams/{id}` - Delete exam (Teacher/Admin)

#### Exam Sessions
- `POST /api/sessions/start` - Start exam session
- `GET /api/sessions/{id}` - Get session details

#### Submissions
- `POST /api/submissions` - Submit exam answers
- `GET /api/submissions/{id}` - Get submission details

#### Monitoring
- `GET /api/sessions/{id}/events` - Get monitoring events
- `GET /api/sessions/{id}/behavior-report` - Get behavior analysis

## AI Proctoring Details

### Frame Analysis
Every 5 seconds, the system:
1. Captures webcam frame
2. Optionally captures screen (if enabled)
3. Sends to AI model (OpenAI GPT-4 Vision or Qwen3-VL)
4. Analyzes for suspicious behavior
5. Generates alerts if confidence threshold exceeded

### Alert Types

| Type | Description | Severity |
|------|-------------|----------|
| `looking_away` | Student looking away from screen | 1-3 |
| `multiple_people` | Additional people detected | 4-5 |
| `phone_detected` | Phone or device in use | 3-4 |
| `reading_from_material` | Books/notes visible | 3-4 |
| `tab_switch` | Browser tab/window change | 2 |
| `suspicious_activity` | Other suspicious behavior | 2-4 |

### Behavioral Analysis Report

After exam completion, generates:
- Total alert count
- Alert breakdown by type
- Risk score (0-10)
- Timeline of all events
- Summary and recommendation

### Auto-Submission

Exam auto-submits when:
- Timer expires
- Cheating score exceeds threshold (default: 10)
- Too many high-severity alerts

## Security Considerations

### Browser Security
- Fullscreen mode enforced
- Tab switching detected and logged
- Copy/paste disabled
- Right-click disabled
- Keyboard shortcuts blocked (F12, Ctrl+Shift+I, etc.)
- Print screen disabled

### Video Recording
- Continuous webcam recording
- Stored securely in S3
- Accessible only to teachers/admins
- Auto-deleted after retention period

### Data Privacy
- Video data encrypted at rest
- Access controlled via JWT
- GDPR/privacy compliant storage
- Students notified of monitoring

## Customization

### Adjusting AI Sensitivity

In `.env`:
```env
# Higher = fewer false positives, might miss some cheating
# Lower = more sensitive, might have false positives
ALERT_CONFIDENCE_THRESHOLD=0.7

# Number of alerts before auto-submit
CHEATING_THRESHOLD_AUTO_SUBMIT=10
```

### Adding Custom Question Types

1. Add type to `models.py`:
```python
class QuestionType(str, enum.Enum):
    # ... existing types
    CUSTOM_TYPE = "custom_type"
```

2. Add UI component in `TakeExam.tsx`

3. Add grading logic in `main.py`

### Customizing UI Theme

Edit `tailwind.config.js`:
```javascript
theme: {
  extend: {
    colors: {
      primary: {
        // Your custom colors
      }
    }
  }
}
```

## Deployment

### Production Checklist

- [ ] Change `SECRET_KEY` in .env
- [ ] Set up production PostgreSQL database
- [ ] Configure AWS S3 bucket
- [ ] Set up HTTPS/SSL
- [ ] Configure CORS for production domain
- [ ] Set up monitoring/logging
- [ ] Configure backup strategy
- [ ] Set up CDN for static assets
- [ ] Enable rate limiting
- [ ] Set up automated backups

### Docker Deployment

Coming soon!

## Troubleshooting

### Camera Not Working
- Ensure HTTPS is used (required for camera access)
- Check browser permissions
- Try different browser

### Socket.IO Connection Issues
- Check CORS settings
- Verify backend is running
- Check firewall rules

### AI Detection Not Working
- Verify OpenAI/Qwen API key is valid
- Check API rate limits
- Review confidence threshold settings

## Performance Optimization

### For Large Scale
- Use Redis for session storage
- Implement CDN for static assets
- Use database connection pooling
- Implement caching for exam data
- Use WebRTC for peer-to-peer video streaming
- Implement load balancing

## Future Enhancements

- [ ] Mobile app support
- [ ] Biometric authentication
- [ ] Advanced analytics dashboard
- [ ] Integration with LMS (Canvas, Moodle, etc.)
- [ ] Multi-language support
- [ ] Accessibility improvements
- [ ] Video conferencing for oral exams
- [ ] Plagiarism detection for essays
- [ ] Code similarity detection
- [ ] Peer review system

## License

MIT License - feel free to use for commercial or personal projects

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Contact: support@examplatform.com

## Credits

Built with:
- FastAPI
- React
- OpenAI GPT-4 Vision
- Socket.IO
- Tailwind CSS

## Disclaimer

This platform is designed for authorized educational use. Users are responsible for ensuring compliance with local privacy laws and regulations regarding video recording and monitoring.

# Quick Start Guide

Get your exam platform up and running in 5 minutes!

## Prerequisites

**Required:**
- Python 3.9+
- Node.js 18+
- PostgreSQL 14+
- **Ollama** with Qwen3-VL model (free local AI)

**Optional:**
- OpenAI API key (cloud alternative)
- AWS S3 (for evidence storage)

## Automated Setup

```bash
# Clone or navigate to the project
cd exam-platform

# Run setup script
./setup.sh
```

## Manual Setup

### 1. Database Setup

```bash
# Create PostgreSQL database
createdb exam_platform

# Or using psql
psql -U postgres
CREATE DATABASE exam_platform;
\q
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Edit with your settings
```

**Required .env variables:**
```env
DATABASE_URL=postgresql://user:password@localhost:5432/exam_platform
SECRET_KEY=your-random-secret-key-here

# Ollama (Default - Free & Local)
USE_OLLAMA=true
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-vl:8b
```

**Setup Ollama (Required):**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull Qwen3-VL model
ollama pull qwen2.5-vl:8b

# Start Ollama server
ollama serve
```

**Optional .env variables:**
```env
# For AWS S3 storage (evidence screenshots)
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
S3_BUCKET_NAME=exam-recordings

# Alternative: Use OpenAI instead of Ollama
USE_OLLAMA=false
OPENAI_API_KEY=sk-your-openai-api-key
```

### 3. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install
```

### 4. Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python main.py
# Server runs on http://localhost:8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
# App runs on http://localhost:5173
```

## First Login

### Create Admin Account

1. Go to http://localhost:5173
2. Click "Sign up"
3. Fill in details:
   - Full Name: Admin User
   - Email: admin@example.com
   - Username: admin
   - Password: admin123
4. Login

### Manually Set Admin Role (if needed)

```bash
# Connect to database
psql exam_platform

# Update user role
UPDATE users SET role = 'admin' WHERE username = 'admin';
\q
```

## Create Your First Exam

1. Login as admin/teacher
2. Click "Create Exam"
3. Fill in exam details:
   - Title
   - Description
   - Duration
   - Start/End time
4. Add questions:
   - MCQ (Multiple Choice)
   - Short Answer
   - Long Answer
   - Coding Questions
5. Save exam
6. Enroll students

## Take an Exam (Student View)

1. Login as student
2. View available exams on dashboard
3. Click "Take Exam" on active exam
4. Grant camera permission
5. Read instructions
6. Start exam
7. Answer questions
8. Submit

## Monitor Exams (Admin/Teacher View)

1. Login as admin/teacher
2. Go to "Admin Panel"
3. Select exam to monitor
4. View:
   - Active sessions
   - Live camera feeds
   - Real-time alerts
   - Cheating scores
5. Review behavior reports after exam

## Testing AI Detection

The AI will detect:

1. **Looking away** - Look away from screen for 3-5 seconds
2. **Phone detection** - Hold phone in front of camera
3. **Multiple people** - Have someone else enter frame
4. **Reading material** - Show a book or notes to camera
5. **Tab switching** - Switch browser tabs (automatically detected)

Alerts appear in real-time on the proctoring dashboard.

## Common Issues

### Camera not working
- Use HTTPS in production (required for camera access)
- Check browser permissions
- Allow camera access when prompted

### Socket.IO connection failed
- Check backend is running
- Verify CORS settings in backend/.env
- Check firewall settings

### Database connection error
- Ensure PostgreSQL is running
- Check DATABASE_URL in .env
- Verify database exists

### AI detection not working
- Verify OpenAI/Qwen API key is valid
- Check API quota/limits
- Review confidence threshold in .env

## Production Deployment

### Security Checklist

- [ ] Change SECRET_KEY to a strong random value
- [ ] Use production PostgreSQL database
- [ ] Set up SSL/HTTPS
- [ ] Configure AWS S3 for video storage
- [ ] Update CORS_ORIGINS to production domain
- [ ] Enable rate limiting
- [ ] Set up database backups
- [ ] Configure monitoring/logging
- [ ] Review privacy compliance

### Environment Variables

Update `.env` for production:

```env
DATABASE_URL=postgresql://prod_user:strong_pass@db.example.com:5432/exam_platform
SECRET_KEY=<generate-strong-random-key>
OPENAI_API_KEY=<your-production-key>
AWS_ACCESS_KEY_ID=<production-aws-key>
AWS_SECRET_ACCESS_KEY=<production-aws-secret>
S3_BUCKET_NAME=exam-platform-prod
CORS_ORIGINS=["https://exam.yourdomain.com"]
```

### Deploy Backend

```bash
# Using gunicorn
pip install gunicorn
gunicorn main:socket_app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Or using systemd service
sudo nano /etc/systemd/system/exam-platform.service
sudo systemctl enable exam-platform
sudo systemctl start exam-platform
```

### Deploy Frontend

```bash
# Build for production
npm run build

# Serve with nginx or any static server
# The build folder contains optimized static files
```

## Next Steps

- Read full documentation in [README.md](README.md)
- Explore API docs at http://localhost:8000/docs
- Customize UI theme in `tailwind.config.js`
- Add custom question types
- Configure advanced AI settings

## Support

For issues or questions:
- Check the [README.md](README.md) for detailed documentation
- Review the API docs
- Open an issue on GitHub

## License

MIT License - Free for commercial and personal use

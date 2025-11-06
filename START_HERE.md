# 🚀 START HERE - Quick Setup with Local AI

This exam platform uses **Ollama** for local AI proctoring - completely **free** and **private**!

## What You Need

- ✅ PostgreSQL database
- ✅ Ollama with Qwen3-VL model
- ✅ Python 3.9+ and Node.js 18+

## 5-Minute Setup

### 1. Install Ollama & Model

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull Qwen3-VL vision model (3-4GB download)
ollama pull qwen2.5-vl:8b

# Start Ollama server
ollama serve
```

Leave this terminal running!

### 2. Setup Database

```bash
# Create PostgreSQL database
createdb exam_platform
```

### 3. Run Setup Script

```bash
cd exam-platform
./setup.sh
```

### 4. Configure Environment

Edit `backend/.env`:

```env
# Database - UPDATE WITH YOUR CREDENTIALS
DATABASE_URL=postgresql://YOUR_USER:YOUR_PASSWORD@localhost:5432/exam_platform

# JWT Secret - CHANGE THIS
SECRET_KEY=change-this-to-random-string

# Ollama (Already configured - no changes needed!)
USE_OLLAMA=true
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-vl:8b
```

### 5. Load Sample Data (Optional)

```bash
cd backend
source venv/bin/activate.fish  # or: source venv/bin/activate
python seed_data.py
```

This creates test accounts:
- **Admin:** admin / admin123
- **Teacher:** teacher / teacher123
- **Students:** student1-5 / student123

### 6. Start the Platform

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate.fish
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### 7. Open & Test

🌐 Open: http://localhost:5173

Login with: **student1** / **student123**

Take the sample exam and test AI detection by:
- Looking away from screen
- Holding phone in view
- Having someone else enter frame

## Test Ollama Setup

Before starting, verify Ollama is working:

```bash
cd backend
source venv/bin/activate.fish
python test_ollama.py
```

Should show:
```
✅ Ollama is running
✅ Model 'qwen2.5-vl:8b' is installed
✅ Model inference working
✅ AIProctorService initialized
```

## Troubleshooting

### Ollama not running?
```bash
# Start Ollama
ollama serve

# Check status
curl http://localhost:11434/api/tags
```

### Model not found?
```bash
# List installed models
ollama list

# Pull the model
ollama pull qwen2.5-vl:8b

# Try alternative if above doesn't work:
ollama pull qwen2-vl:8b
```

### Database connection error?
- Check PostgreSQL is running
- Verify DATABASE_URL in `.env`
- Ensure database exists: `psql -l`

### Port already in use?
- Backend (8000): Change in `main.py`
- Frontend (5173): Change in `vite.config.ts`

## What's Next?

📚 **Full Documentation:** [README.md](README.md)
🔧 **Ollama Details:** [OLLAMA_SETUP.md](OLLAMA_SETUP.md)
⚡ **Quick Reference:** [QUICKSTART.md](QUICKSTART.md)
🏗️ **Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)

## Key Features

✅ **AI Proctoring** - Detects looking away, phones, multiple people
✅ **Secure Browser** - Prevents tab switching, copy/paste
✅ **Real-time Alerts** - Live monitoring for teachers
✅ **Auto-grading** - Instant results for MCQ questions
✅ **Dark Mode** - Modern, clean UI
✅ **100% Local** - No cloud APIs, no costs, complete privacy

## Need Help?

1. Check the logs in terminal
2. Run `python test_ollama.py` to verify setup
3. See [README.md](README.md) for detailed docs
4. See [OLLAMA_SETUP.md](OLLAMA_SETUP.md) for Ollama troubleshooting

---

**Happy Testing!** 🎉

*Remember: Ollama server must be running (`ollama serve`) for AI proctoring to work.*

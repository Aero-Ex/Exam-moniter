# Ollama Setup Guide for Exam Platform

This guide will help you set up the exam platform with local AI proctoring using Ollama and Qwen3-VL 8B.

## Why Ollama?

✅ **No API Keys Required** - Everything runs locally
✅ **Privacy** - No data sent to external services
✅ **No Costs** - No API usage fees
✅ **Fast** - Direct local inference
✅ **Offline** - Works without internet

## Prerequisites

- Ollama installed on your system
- At least 8GB RAM (16GB recommended)
- GPU recommended but not required

## Step 1: Install Ollama (if not already installed)

### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### macOS
```bash
brew install ollama
```

### Windows
Download from https://ollama.com/download

## Step 2: Pull Qwen3-VL Model

The model name can be `qwen3-vl:8b` or `qwen3-vl:8b` depending on availability.

```bash
# Try this first (Qwen 2.5 VL - newer)
ollama pull qwen3-vl:8b

# If above doesn't work, try:
ollama pull qwen3-vl:8b

# Or try the 7B variant if 8B is not available:
ollama pull qwen3-vl:7b
```

**Check available models:**
```bash
ollama list
```

## Step 3: Start Ollama Server

```bash
# Start Ollama server (if not already running)
ollama serve
```

Ollama will run on `http://localhost:11434` by default.

**Test if Ollama is running:**
```bash
curl http://localhost:11434/api/tags
```

You should see a JSON response with available models.

## Step 4: Configure the Exam Platform

Edit `backend/.env`:

```env
# Use Ollama (enabled by default)
USE_OLLAMA=true
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen3-vl:8b

# Database (required)
DATABASE_URL=postgresql://user:password@localhost:5432/exam_platform
SECRET_KEY=your-secret-key-here

# AWS S3 is OPTIONAL - monitoring works without it
# Screenshots will just not be stored if S3 is not configured
```

**Important:** Update `OLLAMA_MODEL` to match the model you pulled:
- `qwen3-vl:8b` (recommended)
- `qwen3-vl:8b` (alternative)
- `qwen3-vl:7b` (smaller, faster)

## Step 5: Verify Setup

### Test Ollama directly:

```bash
# Test with a simple prompt
ollama run qwen3-vl:8b "Describe what you see" < /path/to/test/image.jpg

# Or using the API
curl http://localhost:11434/api/generate -d '{
  "model": "qwen3-vl:8b",
  "prompt": "What do you see in this image?",
  "images": ["base64_encoded_image_here"]
}'
```

### Test with the exam platform:

1. Start the backend:
```bash
cd backend
source venv/bin/activate.fish  # or activate
python main.py
```

2. Check the logs - you should see:
```
INFO: Application startup complete.
```

3. Take an exam and watch the terminal for AI analysis logs

## Troubleshooting

### Issue: "Error connecting to Ollama"

**Solution:**
1. Make sure Ollama is running: `ollama serve`
2. Check if the port is correct: `curl http://localhost:11434/api/tags`
3. Verify the model is installed: `ollama list`

### Issue: "Model not found"

**Solution:**
1. Pull the model again: `ollama pull qwen3-vl:8b`
2. Update `OLLAMA_MODEL` in `.env` to match the exact model name from `ollama list`

### Issue: Slow response times

**Solutions:**
1. Use a GPU if available
2. Try a smaller model: `qwen3-vl:7b`
3. Reduce monitoring frequency in frontend (change from 5s to 10s)
4. Close other applications to free up RAM

### Issue: High CPU/RAM usage

**Solutions:**
1. Use smaller model variant
2. Increase monitoring interval
3. Ensure you have sufficient RAM (16GB recommended)
4. Close other applications

### Issue: Model gives inconsistent results

**Solutions:**
1. Adjust `ALERT_CONFIDENCE_THRESHOLD` in `.env` (default: 0.6)
2. Try temperature adjustment in `ai_service.py` (default: 0.3)
3. Ensure good lighting for webcam

## Model Alternatives

If Qwen3-VL doesn't work well, you can try other vision models:

### LLaVA (good alternative)
```bash
ollama pull llava:13b
```

Update `.env`:
```env
OLLAMA_MODEL=llava:13b
```

### Bakllava (another option)
```bash
ollama pull bakllava
```

Update `.env`:
```env
OLLAMA_MODEL=bakllava
```

## Performance Optimization

### For Production:

1. **Use GPU acceleration:**
   - Ollama automatically uses GPU if available
   - Check: `nvidia-smi` (NVIDIA) or `rocm-smi` (AMD)

2. **Allocate more RAM to Ollama:**
```bash
# Set environment variable before starting
OLLAMA_MAX_LOADED_MODELS=1
OLLAMA_NUM_PARALLEL=2
ollama serve
```

3. **Keep model loaded:**
   - First request loads model (slow)
   - Subsequent requests are fast
   - Keep Ollama running continuously

4. **Adjust monitoring interval:**
   - Default: 5 seconds
   - Can increase to 10s for less load
   - Edit `TakeExam.tsx`: Change `5000` to `10000`

## Monitoring Performance

### Check Ollama logs:
```bash
# Linux/Mac
journalctl -u ollama -f

# Or check the console where ollama serve is running
```

### Monitor system resources:
```bash
# CPU and RAM usage
htop

# GPU usage (if available)
nvidia-smi -l 1
```

## Comparison: Ollama vs OpenAI

| Feature | Ollama (Local) | OpenAI (Cloud) |
|---------|---------------|----------------|
| Cost | Free | ~$0.01 per image |
| Privacy | Complete | Data sent to OpenAI |
| Speed | Fast (local) | Network dependent |
| Quality | Very Good | Excellent |
| Setup | Model download | API key only |
| Offline | ✅ Works | ❌ Needs internet |

## Advanced Configuration

### Custom System Prompt

Edit `backend/ai_service.py` in the `_analyze_with_ollama` method to customize the AI's behavior:

```python
prompt = """Your custom instructions here..."""
```

### Adjust Detection Sensitivity

In `backend/.env`:
```env
# Lower = more sensitive (more alerts)
# Higher = less sensitive (fewer alerts)
ALERT_CONFIDENCE_THRESHOLD=0.6

# Number of alerts before auto-submit
CHEATING_THRESHOLD_AUTO_SUBMIT=10
```

## Support

### Check Ollama Status:
```bash
ollama list  # List installed models
ollama ps    # Show running models
```

### Get Help:
- Ollama docs: https://ollama.com/docs
- Exam platform docs: README.md
- GitHub issues: [Your repo]

## Summary

1. ✅ Install Ollama
2. ✅ Pull Qwen3-VL model: `ollama pull qwen3-vl:8b`
3. ✅ Start Ollama: `ollama serve`
4. ✅ Configure `.env`: Set `USE_OLLAMA=true`
5. ✅ Start exam platform
6. ✅ Test with an exam

**That's it! You now have a fully local AI-powered exam proctoring system!** 🎉

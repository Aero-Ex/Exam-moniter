#!/bin/bash

echo "======================================"
echo "Exam Platform Setup Script"
echo "======================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3.9 or higher.${NC}"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}Node.js is not installed. Please install Node.js 18 or higher.${NC}"
    exit 1
fi

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}Warning: PostgreSQL CLI not found. Make sure PostgreSQL is installed and running.${NC}"
fi

echo -e "${GREEN}✓ Prerequisites check passed${NC}"
echo ""

# Backend setup
echo "Setting up backend..."
cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3.11 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate.fish

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create .env from example if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo -e "${YELLOW}⚠ Please edit backend/.env with your configuration${NC}"
fi

cd ..

# Frontend setup
echo ""
echo "Setting up frontend..."
cd frontend

# Install dependencies
echo "Installing Node dependencies..."
npm install

cd ..

echo ""
echo "======================================"
echo -e "${GREEN}Setup completed!${NC}"
echo "======================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Configure your database:"
echo "   $ createdb exam_platform"
echo ""
echo "2. Edit backend/.env with your configuration:"
echo "   - DATABASE_URL"
echo "   - SECRET_KEY"
echo "   - OPENAI_API_KEY (or QWEN_API_KEY)"
echo "   - AWS credentials (optional)"
echo ""
echo "3. Start the backend server:"
echo "   $ cd backend"
echo "   $ source venv/bin/activate.fish"
echo "   $ python main.py"
echo ""
echo "4. In a new terminal, start the frontend:"
echo "   $ cd frontend"
echo "   $ npm run dev"
echo ""
echo "5. Open your browser at http://localhost:5173"
echo ""
echo -e "${GREEN}Happy testing!${NC}"

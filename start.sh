#!/bin/bash

echo "🚀 Starting Smart Job Application Tracker..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+ first."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

# Start backend
echo "📡 Starting backend server..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "env" ]; then
    echo "🔧 Creating Python virtual environment..."
    python3 -m venv env
fi

# Activate virtual environment
source env/bin/activate

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found in backend directory."
    echo "   Please copy env.example to .env and configure your Google OAuth credentials."
    echo "   See README.md for setup instructions."
fi

# Start backend server in background
echo "🚀 Starting FastAPI server on http://localhost:8000"
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend
echo "🌐 Starting frontend server..."
cd ../frontend

# Install dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Start frontend server
echo "🚀 Starting React development server on http://localhost:5173"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Smart Job Application Tracker is running!"
echo ""
echo "📱 Frontend: http://localhost:5173"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Servers stopped."
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Wait for both processes
wait 
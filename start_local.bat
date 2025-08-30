@echo off
echo 🚀 Starting AI Coastal Threat Alert System...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.9+ first.
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed. Please install Node.js 18+ first.
    pause
    exit /b 1
)

REM Check if npm is installed
npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ npm is not installed. Please install npm first.
    pause
    exit /b 1
)

echo ✅ Prerequisites check passed!

REM Create necessary directories
echo 📁 Creating necessary directories...
if not exist "backend\data\uploads" mkdir "backend\data\uploads"
if not exist "backend\data\models" mkdir "backend\data\models"
if not exist "frontend\build" mkdir "frontend\build"

REM Start Backend
echo 🐍 Starting FastAPI Backend...
cd backend

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📥 Installing Python dependencies...
pip install -r requirements.txt

REM Start backend in background
echo 🚀 Starting backend server on http://localhost:8000
start "Backend Server" cmd /k "uvicorn main:app --reload --host 0.0.0.0 --port 8000"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start Frontend
echo ⚛️  Starting React Frontend...
cd ..\frontend

REM Install dependencies
echo 📥 Installing Node.js dependencies...
npm install

REM Start frontend
echo 🚀 Starting frontend server on http://localhost:3000
start "Frontend Server" cmd /k "npm start"

echo.
echo 🎉 System is starting up!
echo.
echo 📊 Backend API: http://localhost:8000
echo 📚 API Docs: http://localhost:8000/docs
echo 🌐 Frontend: http://localhost:3000
echo.
echo ⏳ Please wait for both services to fully start...
echo.
echo Press any key to exit...
pause >nul



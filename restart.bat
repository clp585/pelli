@echo off
REM Batch script to restart the AI Agent Flask application
REM Usage: restart.bat

echo 🔄 Restarting AI Agent...

REM Check if port 5000 is in use and kill the process
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000 ^| findstr LISTENING') do (
    echo 🛑 Stopping process on port 5000 (PID: %%a)...
    taskkill /F /PID %%a >nul 2>&1
    timeout /t 2 /nobreak >nul
)

REM Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    echo ✅ Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo ⚠️  Virtual environment not found. Make sure venv is set up.
)

REM Set FLASK_DEBUG for auto-reload (development mode)
set FLASK_DEBUG=true

REM Start Flask app
echo 🚀 Starting Flask application...
echo 📍 Server will be available at: http://localhost:5000
echo 💡 Press Ctrl+C to stop the server
echo.

python app.py


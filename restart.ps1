# PowerShell script to restart the AI Agent Flask application
# Usage: .\restart.ps1

Write-Host "🔄 Restarting AI Agent..." -ForegroundColor Cyan

# Check if Flask is running on port 5000
$process = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue
if ($process) {
    Write-Host "⚠️  Port 5000 is in use. Attempting to find and stop Flask process..." -ForegroundColor Yellow
    $flaskProcess = Get-Process | Where-Object { $_.Path -like "*python*" -and $_.CommandLine -like "*app.py*" } -ErrorAction SilentlyContinue
    if ($flaskProcess) {
        Write-Host "🛑 Stopping Flask process (PID: $($flaskProcess.Id))..." -ForegroundColor Yellow
        Stop-Process -Id $flaskProcess.Id -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }
}

# Activate virtual environment
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "✅ Activating virtual environment..." -ForegroundColor Green
    & "venv\Scripts\Activate.ps1"
} else {
    Write-Host "⚠️  Virtual environment not found. Make sure venv is set up." -ForegroundColor Yellow
}

# Set FLASK_DEBUG for auto-reload (development mode)
$env:FLASK_DEBUG = "true"

# Start Flask app
Write-Host "🚀 Starting Flask application..." -ForegroundColor Green
Write-Host "📍 Server will be available at: http://localhost:5000" -ForegroundColor Cyan
Write-Host "💡 Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

python app.py


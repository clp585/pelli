# 🔄 Restart Guide for AI Agent

## Best Practices for Restarting After Fixes

### 🎯 Quick Restart Methods

#### **Method 1: Using Restart Scripts (Recommended)**
```powershell
# PowerShell (Windows)
.\restart.ps1

# OR Batch file
restart.bat
```

#### **Method 2: Manual Restart**
```powershell
# 1. Stop the current server (if running)
# Press Ctrl+C in the terminal where Flask is running

# 2. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 3. Start Flask with auto-reload (development)
$env:FLASK_DEBUG = "true"
python app.py
```

#### **Method 3: Using Flask CLI (Recommended for Development)**
```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Set environment variable
$env:FLASK_DEBUG = "true"
$env:FLASK_APP = "app.py"

# Run with auto-reload
flask run --host=0.0.0.0 --port=5000 --reload
```

---

### 🔧 Development vs Production

#### **Development Mode (Auto-Reload Enabled)**
```powershell
# Enable auto-reload - server restarts automatically on code changes
$env:FLASK_DEBUG = "true"
python app.py
```

**Benefits:**
- ✅ Automatically restarts when you save code changes
- ✅ Shows detailed error pages
- ✅ Interactive debugger on errors
- ✅ No manual restart needed

**⚠️ Security Note:** Never use in production!

#### **Production Mode (No Auto-Reload)**
```powershell
# Production mode - no auto-reload
$env:FLASK_DEBUG = "false"  # or don't set it (defaults to false)
python app.py
```

**Benefits:**
- ✅ More secure (no debug info exposed)
- ✅ Better performance
- ✅ Production-ready

---

### 🛑 Stopping the Server

**Method 1: Keyboard Interrupt**
- Press `Ctrl+C` in the terminal where Flask is running
- Wait for graceful shutdown (usually 1-2 seconds)

**Method 2: Kill Process (if Ctrl+C doesn't work)**
```powershell
# Find Flask process
Get-Process | Where-Object {$_.Path -like "*python*"}

# Kill by PID (replace XXXX with actual PID)
Stop-Process -Id XXXX -Force

# OR kill all Python processes (use with caution!)
Get-Process python | Stop-Process -Force
```

**Method 3: Kill by Port**
```powershell
# Find process using port 5000
$connection = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue
if ($connection) {
    Stop-Process -Id $connection.OwningProcess -Force
}
```

---

### ✅ Verification After Restart

1. **Check Server is Running:**
   ```powershell
   # Test health endpoint
   curl http://localhost:5000/health
   # OR open in browser: http://localhost:5000
   ```

2. **Check Logs:**
   - Look for: `* Running on http://0.0.0.0:5000`
   - No import errors or syntax errors
   - All modules loaded successfully

3. **Test a Simple Request:**
   - Open browser: `http://localhost:5000`
   - Should see the UI without errors

---

### 🚀 Recommended Development Workflow

1. **Initial Setup:**
   ```powershell
   # Activate venv
   .\venv\Scripts\Activate.ps1
   
   # Set development mode
   $env:FLASK_DEBUG = "true"
   
   # Start server
   python app.py
   ```

2. **After Making Code Changes:**
   - If `FLASK_DEBUG=true`: Server auto-restarts (just wait 1-2 seconds)
   - If `FLASK_DEBUG=false`: Stop (Ctrl+C) and restart manually

3. **After Installing New Packages:**
   ```powershell
   # Always restart after pip install
   pip install <package>
   # Then restart server
   ```

4. **After Environment Variable Changes:**
   ```powershell
   # Restart required for .env changes
   # Stop server, update .env, restart
   ```

---

### 🔍 Troubleshooting

#### **Port Already in Use:**
```powershell
# Error: "Address already in use"
# Solution: Kill process on port 5000
$connection = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue
if ($connection) {
    Stop-Process -Id $connection.OwningProcess -Force
}
```

#### **Module Import Errors After Restart:**
```powershell
# Clear Python cache
Get-ChildItem -Path . -Include __pycache__ -Recurse -Directory | Remove-Item -Recurse -Force
Get-ChildItem -Path . -Include *.pyc -Recurse -File | Remove-Item -Force

# Then restart
```

#### **Changes Not Reflecting:**
- Check if `FLASK_DEBUG=true` is set
- Verify file was saved
- Check for syntax errors in terminal
- Try manual restart (Ctrl+C, then restart)

---

### 📝 Quick Reference

| Action | Command |
|--------|---------|
| **Start (Dev)** | `$env:FLASK_DEBUG="true"; python app.py` |
| **Start (Prod)** | `$env:FLASK_DEBUG="false"; python app.py` |
| **Stop** | `Ctrl+C` |
| **Restart Script** | `.\restart.ps1` |
| **Check Health** | `curl http://localhost:5000/health` |
| **Kill Port 5000** | See troubleshooting above |

---

### 💡 Pro Tips

1. **Use Auto-Reload for Development:** Set `FLASK_DEBUG=true` to avoid manual restarts
2. **Keep Terminal Open:** Don't close the terminal where Flask is running
3. **Watch for Errors:** Check terminal output after restart for any import/syntax errors
4. **Test Immediately:** After restart, test a simple request to verify it's working
5. **Use Health Endpoint:** `/health` endpoint confirms server is running correctly

---

**🎯 Best Practice:** Use the restart scripts (`restart.ps1` or `restart.bat`) for consistent, reliable restarts!


# Remaining Improvements for AI Lighting Agent

This document outlines the remaining improvements that can be made to enhance the AI Lighting Agent.

## 🔴 Critical Security & Stability (Implement Immediately)

### 1. Job Memory Leak Fix
**Status**: ❌ Not Implemented  
**Priority**: CRITICAL  
**Impact**: Memory grows unbounded, server crashes over time

**Current Issue**: `JOBS = {}` in `app.py` never cleans up completed jobs.

**Solution**:
```python
# Replace JOBS = {} with:
from agent_tools.cache import TTLCache
JOBS = TTLCache(ttl_seconds=3600, max_size=1000)

# Update all JOBS[job_id] = {...} to:
JOBS.set(job_id, {'queue': queue.Queue()})

# Update all JOBS.get(job_id) to:
JOBS.get(job_id)
```

---

### 2. Flask Debug Mode
**Status**: ❌ Not Implemented  
**Priority**: CRITICAL  
**Impact**: Security vulnerability in production

**Current Issue**: `app.run(debug=True)` hardcoded.

**Solution**:
```python
DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
app.run(host="0.0.0.0", port=5000, debug=DEBUG)
```

---

### 3. Request Size Limits
**Status**: ❌ Not Implemented  
**Priority**: CRITICAL  
**Impact**: DoS vulnerability

**Solution**:
```python
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

# Add validation in render_api() and preview_api()
for file in files:
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > 50 * 1024 * 1024:
        return jsonify({"status": "error", "message": "File too large (max 50MB)"}), 400
```

---

### 4. CSRF Protection
**Status**: ❌ Not Implemented  
**Priority**: CRITICAL  
**Impact**: Cross-site request forgery attacks

**Solution**:
```python
from flask_wtf.csrf import CSRFProtect
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', os.urandom(32).hex())
csrf = CSRFProtect(app)
```

---

### 5. Health Check Endpoint
**Status**: ❌ Not Implemented  
**Priority**: HIGH  
**Impact**: Monitoring and deployment health checks

**Solution**:
```python
@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "cache_size": SESSION_MEMORY.size() if hasattr(SESSION_MEMORY, 'size') else len(SESSION_MEMORY),
        "active_jobs": len(JOBS) if isinstance(JOBS, dict) else JOBS.size(),
        "uptime": time.time() - start_time
    })
```

---

## 🟡 High-Value Features

### 6. Rate Limiting
**Status**: ❌ Not Implemented  
**Priority**: HIGH  
**Impact**: Prevent abuse, ensure fair usage

**Solution**:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route("/api/render", methods=["POST"])
@limiter.limit("5 per minute")
def render_api():
    # ...
```

---

### 7. Parallel Processing
**Status**: ❌ Not Implemented  
**Priority**: HIGH  
**Impact**: Faster batch processing

**Current**: Processes images sequentially  
**Improvement**: Use ThreadPoolExecutor to process multiple images concurrently

**Solution**:
```python
from concurrent.futures import ThreadPoolExecutor

def process_render_job(job_id, file_paths, options):
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for f_path in file_paths:
            future = executor.submit(process_single_image, f_path, options, job_id)
            futures.append(future)
        # Wait for all to complete
```

---

### 8. Image Caching
**Status**: ❌ Not Implemented  
**Priority**: MEDIUM-HIGH  
**Impact**: Avoid re-processing identical images, save costs

**Solution**:
- Hash input image + settings
- Check if result exists in cache
- Return cached result if found
- Only call API if cache miss

---

### 9. Better Error Messages
**Status**: ⚠️ Partial  
**Priority**: MEDIUM  
**Impact**: User experience

**Improvement**: User-friendly error messages with actionable suggestions

**Solution**:
```python
ERROR_MESSAGES = {
    "FileNotFoundError": "The image file could not be found. Please check the file path.",
    "ValidationError": "Invalid settings. Please check your input and try again.",
    "RateLimitError": "Too many requests. Please wait a moment and try again.",
    "ServerError": "The AI service is temporarily unavailable. Please try again in a few minutes.",
}

def get_user_friendly_error(error: Exception) -> str:
    error_type = type(error).__name__
    return ERROR_MESSAGES.get(error_type, f"An error occurred: {str(error)}")
```

---

### 10. Disk Space Checks
**Status**: ❌ Not Implemented  
**Priority**: MEDIUM  
**Impact**: Prevent disk full errors

**Solution**:
```python
import shutil

def check_disk_space(folder_path, min_free_gb=1):
    """Check if folder has enough free space."""
    stat = shutil.disk_usage(folder_path)
    free_gb = stat.free / (1024**3)
    if free_gb < min_free_gb:
        raise ValidationError(f"Insufficient disk space. Need at least {min_free_gb}GB free.")
    return True
```

---

## 🟢 Quality of Life & Advanced Features

### 11. Undo/Redo System
**Status**: ❌ Not Implemented  
**Priority**: MEDIUM  
**Impact**: Experimentation freedom

**Features**:
- Undo last refinement
- Redo chain
- History navigation
- Branch from any point

---

### 12. Real-time Preview Updates
**Status**: ❌ Not Implemented  
**Priority**: MEDIUM  
**Impact**: Faster iteration

**Features**:
- Live preview as sliders change
- Instant feedback on parameter changes
- "Apply to all" option for batch edits

---

### 13. Advanced Search & Filtering
**Status**: ⚠️ Basic  
**Priority**: MEDIUM  
**Impact**: Organization

**Enhancements**:
- Full-text search in gallery
- Tag system for organization
- Smart collections (auto-grouped)
- Date range filtering

---

### 14. Lighting Analysis Tools
**Status**: ❌ Not Implemented  
**Priority**: MEDIUM  
**Impact**: Professional workflow

**Features**:
- Histogram analysis (brightness distribution)
- Color temperature visualization
- Shadow analysis
- Highlight detection
- Lighting consistency checker

---

### 15. Time-of-Day Progression
**Status**: ❌ Not Implemented  
**Priority**: LOW-MEDIUM  
**Impact**: Visualization

**Features**:
- Generate all times of day automatically
- Create time-lapse sequence
- Export as video/GIF
- Smooth transitions between times

---

### 16. Usage Analytics Dashboard
**Status**: ❌ Not Implemented  
**Priority**: MEDIUM  
**Impact**: Optimization

**Metrics**:
- Most used lighting modes
- Popular style combinations
- Average render time
- Success rate by settings
- Cost per successful render
- Peak usage times

---

### 17. Budget Alerts
**Status**: ❌ Not Implemented  
**Priority**: MEDIUM  
**Impact**: Cost control

**Features**:
- Set daily/weekly/monthly budgets
- Email/notification alerts when approaching limit
- Auto-pause rendering at budget limit
- Budget reset schedules

---

### 18. Webhook Notifications
**Status**: ❌ Not Implemented  
**Priority**: LOW-MEDIUM  
**Impact**: Integration

**Features**:
- Webhook on render completion
- Webhook on errors
- Custom webhook URLs per job
- Retry failed webhooks

---

### 19. Image Quality Scoring
**Status**: ⚠️ Partial (critic only)  
**Priority**: MEDIUM  
**Impact**: Quality assurance

**Enhancements**:
- Detailed quality metrics
- Consistency scoring
- Geometry preservation score
- Lighting accuracy score
- User satisfaction tracking

---

### 20. Collaborative Features
**Status**: ❌ Not Implemented  
**Priority**: LOW  
**Impact**: Team workflow

**Features**:
- Share renders via link
- Comments/annotations on images
- Approval workflow
- Team preset library
- User roles and permissions

---

## 🔧 Technical Improvements

### 21. Database Migration (SQLite)
**Status**: ❌ Not Implemented  
**Priority**: MEDIUM  
**Impact**: Performance, scalability

**Current**: JSON files for storage  
**Improvement**: Migrate to SQLite for better performance

**Benefits**:
- Faster queries
- Better concurrent access
- Indexing for search
- Data integrity

---

### 22. API Response Caching
**Status**: ❌ Not Implemented  
**Priority**: MEDIUM  
**Impact**: Cost savings, speed

**Features**:
- Cache API responses for identical requests
- TTL-based cache invalidation
- Cache hit/miss metrics

---

### 23. Background Job Queue (Celery/Redis)
**Status**: ❌ Not Implemented  
**Priority**: LOW-MEDIUM  
**Impact**: Scalability

**Current**: In-memory threads  
**Improvement**: Use Celery + Redis for distributed job processing

**Benefits**:
- Horizontal scaling
- Job persistence
- Better monitoring
- Retry mechanisms

---

### 24. Logging to File
**Status**: ⚠️ Partial  
**Priority**: MEDIUM  
**Impact**: Debugging, monitoring

**Enhancement**: Add file logging in addition to console

**Solution**:
```python
# In agent_tools/config.py
file_handler = logging.FileHandler('agent.log')
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)
```

---

### 25. Metrics & Monitoring
**Status**: ❌ Not Implemented  
**Priority**: MEDIUM  
**Impact**: Observability

**Features**:
- Prometheus metrics endpoint
- Request duration tracking
- Error rate monitoring
- API call success rate
- Cost per request tracking

---

## 📊 Recommended Implementation Order

### Phase 1: Critical Security (Week 1)
1. ✅ Job memory leak fix
2. ✅ Flask debug mode
3. ✅ Request size limits
4. ✅ CSRF protection
5. ✅ Health check endpoint

### Phase 2: Performance & Reliability (Week 2)
6. ✅ Rate limiting
7. ✅ Parallel processing
8. ✅ Image caching
9. ✅ Better error messages
10. ✅ Disk space checks

### Phase 3: Advanced Features (Week 3+)
11. ✅ Undo/redo system
12. ✅ Real-time preview updates
13. ✅ Advanced search
14. ✅ Lighting analysis tools
15. ✅ Usage analytics

---

## 🎯 Quick Wins (Easy, High Impact)

1. **Job Memory Leak** (30 min) - Use existing TTLCache
2. **Flask Debug Mode** (5 min) - Environment variable
3. **Request Size Limits** (10 min) - Config + validation
4. **Health Check** (15 min) - Simple endpoint
5. **Better Error Messages** (30 min) - Error mapping
6. **Disk Space Checks** (20 min) - shutil.disk_usage

---

*Last Updated: 2025-01-27*


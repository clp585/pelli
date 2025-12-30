# Performance Optimization Plan

## Current Performance Bottlenecks

### 🔴 Critical Issues (Biggest Impact)

1. **Sequential API Calls** - 6-8 API calls per render run sequentially
   - Director Agent (~5-10s)
   - Material Analyst (~5-10s)
   - Global Illumination Analyst (~5-10s)
   - Building Type Analyst (~5-10s)
   - Lighting Expert (~10-20s)
   - Specialized Agents (Shadow, Color, Atmosphere) (~15-30s total)
   - **Total: 45-90 seconds just for analysis before rendering**

2. **No Result Caching** - Same image + parameters processed repeatedly
   - No cache for analysis results
   - No cache for final renders
   - Re-processing identical requests wastes time and API costs

3. **Redundant Analysis** - Agents run even when data exists
   - Material analysis runs even if already provided
   - GI analysis runs even if already provided
   - Building type analysis runs even if already provided

### 🟡 High-Impact Optimizations

4. **Limited Parallelism** - Only 3 workers for batch processing
   - Could increase to 5-10 workers for faster batch processing
   - API rate limits may be the constraint

5. **No Request Batching** - Each agent call is separate
   - Could combine some analysis into single API calls
   - Could use batch API endpoints if available

6. **Image Processing Overhead** - Multiple image analyses
   - Same image analyzed 4+ times by different agents
   - Could analyze once and share results

---

## Optimization Strategies

### Strategy 1: Parallel Agent Execution (HIGHEST IMPACT) ⚡

**Impact**: Reduce analysis time from 45-90s to 15-30s (50-70% faster)

**Implementation**:
- Run independent agents in parallel using ThreadPoolExecutor
- Director, Material, GI, and Building Type can all run simultaneously
- Only Lighting Expert needs to wait for their results

**Code Changes**:
```python
# In render.py, replace sequential calls with parallel execution
from concurrent.futures import ThreadPoolExecutor, as_completed

def run_nano_variant(...):
    # ... existing code ...
    
    # Run independent agents in parallel
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            'director': executor.submit(agent_director, base_img, director_context),
            'material': executor.submit(agent_material_analyst, base_img),
            'gi': executor.submit(agent_gi_analyst, base_img, lighting_mode, location),
            'building_type': executor.submit(agent_building_type_analyst, base_img)
        }
        
        # Wait for all to complete
        results = {}
        for key, future in as_completed(futures.items()):
            try:
                results[key] = future.result()
            except Exception as e:
                logger.warning(f"{key} agent failed: {e}")
                results[key] = None
    
    director_brief = results['director']
    material_analysis = results['material']
    gi_analysis = results['gi']
    building_type_analysis = results['building_type']
    
    # Then run lighting expert with all results
    lighting_specs = agent_lighting_expert(...)
```

**Estimated Speedup**: 50-70% faster analysis phase

---

### Strategy 2: Result Caching (HIGH IMPACT) 💾

**Impact**: Eliminate redundant processing, save API costs

**Implementation**:
- Cache analysis results by image hash + parameters
- Cache final renders by input hash + all parameters
- Use file-based cache with TTL (24 hours)

**Code Changes**:
```python
# Add to agent_tools/cache.py
import hashlib
from PIL import Image

def get_image_hash(image_path: str) -> str:
    """Generate hash from image file."""
    with open(image_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]

def get_analysis_cache_key(image_hash: str, agent_type: str, params: dict) -> str:
    """Generate cache key for analysis results."""
    key_data = {
        'image': image_hash,
        'agent': agent_type,
        'params': params
    }
    return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()

# Cache analysis results
ANALYSIS_CACHE = TTLCache(ttl_seconds=86400, max_size=1000)  # 24 hours

def get_cached_analysis(cache_key: str) -> Optional[str]:
    """Get cached analysis result."""
    return ANALYSIS_CACHE.get(cache_key)

def cache_analysis(cache_key: str, result: str):
    """Cache analysis result."""
    ANALYSIS_CACHE.set(cache_key, result)

# In each agent function:
def agent_material_analyst(base_img: Image.Image) -> str:
    # Generate cache key
    img_hash = get_image_hash_from_pil(base_img)  # Need to save temp file or use in-memory hash
    cache_key = get_analysis_cache_key(img_hash, 'material', {})
    
    # Check cache
    cached = get_cached_analysis(cache_key)
    if cached:
        logger.debug("Material analysis cache hit")
        return cached
    
    # Run analysis
    result = _run_analysis(...)
    
    # Cache result
    cache_analysis(cache_key, result)
    return result
```

**Estimated Speedup**: 100% faster for repeated requests (instant)

---

### Strategy 3: Skip Redundant Analysis (MEDIUM IMPACT) ⏭️

**Impact**: Save 15-30 seconds when data already exists

**Current Issue**: Agents run even when data is provided

**Fix**: Already partially implemented, but ensure it's working correctly

**Code Check**:
```python
# In agent_lighting_expert, ensure we skip analysis when data exists:
if material_analysis:
    # Use provided data - DON'T run agent_material_analyst
    materials = parse_material_analysis(material_analysis)
else:
    # Only run if not provided
    material_analysis_text = agent_material_analyst(base_img)
```

**Estimated Speedup**: 15-30s saved when reusing data

---

### Strategy 4: Increase Parallel Workers (MEDIUM IMPACT) 🚀

**Impact**: Faster batch processing

**Current**: 3 workers max
**Recommended**: 5-10 workers (check API rate limits)

**Code Changes**:
```python
# In app.py, process_render_job function
max_workers = min(5, total_tasks, len(tasks))  # Increase from 3 to 5
```

**Estimated Speedup**: 40-60% faster for batches of 5+ images

---

### Strategy 5: Optimize Image Processing (LOW-MEDIUM IMPACT) 🖼️

**Impact**: Reduce image I/O overhead

**Implementation**:
- Load image once, pass PIL Image object to all agents
- Resize large images before analysis (agents don't need full resolution)
- Cache image loading

**Code Changes**:
```python
# In render.py
base_img = Image.open(image_path)

# Resize for analysis (faster, agents don't need full res)
ANALYSIS_SIZE = (1024, 1024)  # Sufficient for analysis
if base_img.size[0] > ANALYSIS_SIZE[0] or base_img.size[1] > ANALYSIS_SIZE[1]:
    analysis_img = base_img.copy()
    analysis_img.thumbnail(ANALYSIS_SIZE, Image.Resampling.LANCZOS)
else:
    analysis_img = base_img

# Use analysis_img for all agents
director_brief = agent_director(analysis_img, ...)
material_analysis = agent_material_analyst(analysis_img)
# etc.

# Use full base_img only for final render
```

**Estimated Speedup**: 10-20% faster analysis, reduced API costs

---

### Strategy 6: Request Batching (FUTURE) 📦

**Impact**: Combine multiple API calls into one

**Note**: Depends on Gemini API supporting batch requests

**If Available**:
- Combine Director + Material + GI + Building Type into single request
- Use structured output to get all results at once

---

## Implementation Priority

### Phase 1: Quick Wins (Implement First) ⚡
1. **Parallel Agent Execution** - Biggest impact, relatively easy
2. **Skip Redundant Analysis** - Verify it's working
3. **Increase Parallel Workers** - Simple change

**Estimated Total Speedup**: 60-80% faster

### Phase 2: Caching (Implement Second) 💾
4. **Result Caching** - More complex but high value

**Estimated Additional Speedup**: 100% faster for repeated requests

### Phase 3: Optimizations (Implement Third) 🎯
5. **Optimize Image Processing** - Lower impact but still valuable

---

## Recommended Implementation Order

1. ✅ **Parallel Agent Execution** (Strategy 1) - Do this first!
2. ✅ **Increase Parallel Workers** (Strategy 4) - Easy win
3. ✅ **Verify Skip Redundant Analysis** (Strategy 3) - Quick check
4. ⏳ **Result Caching** (Strategy 2) - More work but high value
5. ⏳ **Optimize Image Processing** (Strategy 5) - Nice to have

---

## Expected Performance Improvements

### Current Performance
- Single render: ~60-120 seconds
- Batch of 5 images: ~5-10 minutes

### After Phase 1 Optimizations
- Single render: ~20-40 seconds (60-70% faster)
- Batch of 5 images: ~2-4 minutes (60% faster)

### After Phase 2 (with caching)
- First render: ~20-40 seconds
- Repeated render: ~5-10 seconds (80-90% faster)
- Batch of 5 images: ~2-4 minutes (first time), ~30-60 seconds (cached)

---

## Additional Recommendations

### Monitoring
- Add timing logs to identify slowest operations
- Track cache hit rates
- Monitor API response times

### Configuration
- Make worker count configurable via environment variable
- Make cache TTL configurable
- Add feature flag to enable/disable caching

### Testing
- Test parallel execution with various image sizes
- Test cache behavior with edge cases
- Verify no regressions in output quality


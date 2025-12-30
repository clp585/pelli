# Issue: Standardize Cost Field Naming Across All Job Types

## Problem Statement

The cost field naming is inconsistent across different job types, which creates confusion and complicates UI handling:

- **Render jobs** (`/api/render`): Use `total_cost_usd` in the SSE complete event payload
- **Refine jobs** (`/api/refine`): Use `cost_usd` in the SSE complete event payload
- **Inpaint jobs** (`/api/inpaint`): Use `cost_usd` in the SSE complete event payload
- **Video jobs** (`/api/video`): Use `cost_usd` in the SSE complete event payload
- **Preview jobs** (`/api/preview`): Do not include a cost field in the SSE complete event payload
- **Mashup endpoint** (`/api/mashup`): Use `cost_usd` in JSON response (not SSE)

## Current State

### Backend (`app.py`)

1. **`process_render_job`** (line ~249):
   ```python
   "data": {
       "status": "success",
       "images": formatted_results,  # Each item has cost_usd
       "total_cost_usd": total_cost_usd,  # ← Uses total_cost_usd
       "settings": options
   }
   ```
   Note: Individual image items in `formatted_results` already use `cost_usd` (line ~202).

2. **`process_refine_job`** (line ~311):
   ```python
   "data": {
       "status": "success",
       "image": result_path,
       "cost_usd": cost_usd,  # ← Uses cost_usd
       "original_job_id": original_job_id
   }
   ```

3. **`process_inpaint_job`** (line ~528):
   ```python
   "data": {
       "status": "success",
       "image": result_path,
       "cost_usd": cost_usd  # ← Uses cost_usd
   }
   ```

4. **`process_video_job`** (line ~601):
   ```python
   "data": {
       "status": "success",
       "video": video_url,
       "cost_usd": cost_usd,  # ← Uses cost_usd
       "settings": options,
       "artifact_type": artifact_type,
       "artifact_mime": artifact_mime
   }
   ```

5. **`process_preview_job`** (line ~1049):
   ```python
   "data": {
       "status": "success",
       "preview_path": preview_path,
       "message": "Preview generated..."
       # ← No cost field
   }
   ```

6. **`/api/mashup` endpoint** (line ~799):
   ```python
   return jsonify({
       "status": "success",
       "image": out_path,
       "base_image_name": "mashup_base_" + base_name,
       "cost_usd": cost_usd  # ← Uses cost_usd (JSON response, not SSE)
   })
   ```

### Frontend (`templates/index.html`)

1. **Render jobs** (line ~1923):
   - Accesses `imgData.cost_usd` from individual image items in `displayResults()`
   - Does not use `data.total_cost_usd` from the top-level complete event

2. **Refine jobs** (line ~2594):
   - Accesses `msg.data.cost_usd` directly

3. **Inpaint jobs** (line ~2467):
   - Accesses `msg.data.cost_usd` directly

4. **Video jobs** (line ~1767):
   - Accesses `msg.data.cost_usd` directly

5. **Preview jobs**:
   - No cost display currently

6. **Mashup endpoint** (line ~2733):
   - Accesses `data.cost_usd` from JSON response

## Proposed Solution

### Standardize to `cost_usd` everywhere

**Rationale:**
- `cost_usd` is already used by 5 out of 6 job types
- More consistent with database schema (`agent_tools/storage.py` uses `cost_usd`)
- Simpler and more intuitive naming
- Aligns with the pattern used in video/inpaint/refine jobs

### Changes Required

#### Backend Changes

1. **`process_render_job`** (`app.py` line ~249):
   - Change `"total_cost_usd": total_cost_usd` → `"cost_usd": total_cost_usd`
   - Keep individual image `cost_usd` fields in `formatted_results` unchanged

2. **`process_preview_job`** (`app.py` line ~1049):
   - Add cost calculation (similar to render, but for 1K preview)
   - Add `"cost_usd": cost_usd` to complete event payload

3. **All other job types**: No changes needed (already use `cost_usd`)

#### Frontend Changes

1. **Render jobs** (`templates/index.html`):
   - Current code already uses `imgData.cost_usd` (individual items), which is correct
   - Optionally: Add fallback to `data.cost_usd` for total cost display if needed
   - Maintain backward compatibility by checking both `total_cost_usd` and `cost_usd` during transition

2. **Preview jobs** (`templates/index.html`):
   - Add cost display if cost is added to backend payload

3. **All other job types**: No changes needed (already use `msg.data.cost_usd`)

### Backward Compatibility Strategy

To ensure smooth transition without breaking existing clients:

1. **Backend**: Emit both fields during transition period:
   ```python
   "data": {
       "status": "success",
       "images": formatted_results,
       "cost_usd": total_cost_usd,  # New standardized field
       "total_cost_usd": total_cost_usd,  # Legacy field (deprecated)
       "settings": options
   }
   ```

2. **Frontend**: Check for `cost_usd` first, fallback to `total_cost_usd`:
   ```javascript
   const cost = msg.data.cost_usd ?? msg.data.total_cost_usd;
   ```

3. **Documentation**: Update `PROJECT_SNAPSHOT.md` to reflect the standardized contract

4. **Deprecation**: After sufficient time, remove `total_cost_usd` from backend and fallback from frontend

## Testing Requirements

1. Verify all job types emit `cost_usd` in complete events
2. Verify UI correctly displays costs for all job types
3. Verify backward compatibility works during transition
4. Update smoke tests to check for `cost_usd` (or both during transition)
5. Verify cost tracking in database still works correctly

## Files to Modify

- `app.py`: `process_render_job`, `process_preview_job`
- `templates/index.html`: Render complete handler, preview complete handler
- `export_agent_snapshot.py`: Update snapshot generator to reflect standardized contract
- `scripts/smoke_test.py`: Update contract assertions
- `PROJECT_SNAPSHOT.md`: Will be auto-regenerated

## Related Context

- Video endpoint was recently standardized to use `cost_usd` (commit: "Harden /api/video contract: cost_usd + /output URL + contract smoke test")
- Database schema already uses `cost_usd` consistently (`agent_tools/storage.py`)
- Cost tracking endpoints (`/api/costs`) already use `cost_usd`

## Priority

**Medium** - Improves consistency and maintainability but does not affect functionality if handled with backward compatibility.

## Notes

- Individual render job image items already use `cost_usd` correctly
- The main inconsistency is the top-level `total_cost_usd` in render jobs vs `cost_usd` everywhere else
- Preview jobs currently don't include cost, but should for consistency and user awareness


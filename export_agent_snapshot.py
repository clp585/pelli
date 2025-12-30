#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Export Agent Snapshot Script

Generates a single readable markdown file (PROJECT_SNAPSHOT.md) from the repository
containing: Build Identity, Repo Tree, API Inventory, Options Schema, Key Files, Notes/TODO.
"""

import os
import sys
import re
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Set, Optional

# Set UTF-8 encoding for Windows console output
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Default configuration (can be overridden via CLI)
DEFAULT_PROJECT_ROOT = Path(__file__).parent
DEFAULT_OUTPUT_FILE = DEFAULT_PROJECT_ROOT / "PROJECT_SNAPSHOT.md"

# Exclusion patterns (same as bundler)
EXCLUDE_FOLDERS = {
    '.git',
    'venv',
    '.venv',
    'node_modules',
    '__pycache__',
    'input',
    'output',
    'dist',
}

EXCLUDE_FILE_EXTENSIONS = {
    '.png',
    '.jpg',
    '.jpeg',
    '.webp',
    '.gif',
    '.mp4',
    '.mov',
    '.zip',
}

# Key files to include (if present)
KEY_FILES = [
    'app.py',
    'run_agent.py',
    'main_agent.py',
    'config.yaml',
    'styles.json',
    'requirements.txt',
    'templates/index.html',
]

DEFAULT_MAX_FILE_LENGTH = 12000  # Default truncation limit

# Standard endpoint checklist
NEW_ENDPOINT_CHECKLIST = """## Adding a new endpoint (checklist)

Standard wiring pattern used in this project:

1. Add Flask route (`@app.route("/api/endpoint", methods=["POST"])`)
2. Parse request fields (`request.form.get()`, `request.files.get()`)
3. Create `job_id` and `JOBS` queue (`JOBS.set(job_id, {'queue': queue.Queue()})`)
4. Spawn worker thread (`threading.Thread(target=process_job, args=(...))`)
5. Stream via `/api/stream/<job_id>` (worker calls `q.put()` with progress/complete/error)
6. Serve result via `/output/<path:filename>` (static file serving route)
7. Update UI to call endpoint and listen to stream (EventSource pattern)
"""


def should_exclude(path: Path, exclude_folders: Set[str], exclude_extensions: Set[str]) -> bool:
    """Check if a path should be excluded."""
    path_str = str(path)
    path_name = path.name
    
    # Check if folder name matches excluded folders
    if path_name in exclude_folders:
        return True
    
    # Check if any excluded folder pattern is in the path
    for folder in exclude_folders:
        if folder in path_str:
            return True
    
    # Check for excluded file extensions (case-insensitive)
    if path.is_file() and path.suffix.lower() in exclude_extensions:
        return True
    
    return False


def _build_repo_tree_recursive(root: Path, project_root: Path, exclude_folders: Set[str], exclude_extensions: Set[str], prefix: str = "", is_last: bool = True, max_depth: int = 3, current_depth: int = 0) -> List[str]:
    """Internal recursive helper to build tree lines."""
    if current_depth >= max_depth:
        return []
    
    lines = []
    path_name = root.name if root != project_root else "."
    
    if root != project_root:
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{path_name}/")
        prefix += "    " if is_last else "│   "
    
    if not root.is_dir():
        return lines
    
    # Get all items, sorted: directories first, then files
    try:
        items = sorted(root.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
        # Apply exclusion filter - ensure input/ and output/ are never included
        items = [item for item in items if not should_exclude(item, exclude_folders, exclude_extensions)]
    except PermissionError:
        return lines
    
    # Only show directories at deeper levels, or files at shallow levels
    for i, item in enumerate(items):
        is_last_item = (i == len(items) - 1)
        
        if item.is_dir():
            lines.extend(_build_repo_tree_recursive(
                item, project_root, exclude_folders, exclude_extensions,
                prefix, is_last_item, max_depth, current_depth + 1
            ))
        elif current_depth < 2:  # Show files only at top 2 levels
            connector = "└── " if is_last_item else "├── "
            lines.append(f"{prefix}{connector}{item.name}")
    
    return lines


def build_repo_tree(root: Path, project_root: Path) -> str:
    """
    Build a readable folder tree representation of the repository structure.
    
    Applies exclusion rules to ensure input/ and output/ never appear in the tree.
    Returns a formatted string with the tree structure.
    """
    lines = _build_repo_tree_recursive(root, project_root, EXCLUDE_FOLDERS, EXCLUDE_FILE_EXTENSIONS)
    return '\n'.join(lines)


def _extract_render_api_params(content: str, func_name: str) -> dict:
    """
    Extract request.form.get() and request.files.getlist() keys from a specific function body.
    Best-effort parsing - finds the function and extracts parameter keys.
    """
    form_keys = set()
    files_keys = set()
    
    try:
        # Find the function definition
        func_pattern = rf'def\s+{func_name}\s*\([^)]*\):\s*\n(.*?)(?=\n\n@app\.route|\n\n#|\Z)'
        func_match = re.search(func_pattern, content, re.DOTALL)
        
        if not func_match:
            return {'form_keys': [], 'files_keys': []}
        
        func_body = func_match.group(1)
        
        # Extract request.form.get("key", ...) patterns
        form_pattern = r'request\.form\.get\(["\']([^"\']+)["\']'
        for match in re.finditer(form_pattern, func_body):
            key = match.group(1)
            form_keys.add(key)
        
        # Extract request.files.getlist("key") patterns
        files_pattern = r'request\.files\.getlist\(["\']([^"\']+)["\']'
        for match in re.finditer(files_pattern, func_body):
            key = match.group(1)
            files_keys.add(key)
        
    except Exception as e:
        # Best effort - return empty if parsing fails
        pass
    
    return {
        'form_keys': sorted(list(form_keys)),
        'files_keys': sorted(list(files_keys))
    }


def extract_api_routes(app_file: Path) -> List[dict]:
    """
    Extract Flask route definitions from app.py.
    For /api/render route, also extracts request.form.get() and request.files.getlist() keys.
    """
    routes = []
    
    if not app_file.exists():
        return routes
    
    try:
        content = app_file.read_text(encoding='utf-8', errors='replace')
        
        # Pattern to match @app.route decorators and function definitions
        pattern = r'@app\.route\(["\']([^"\']+)["\'](?:\s*,\s*methods=\[([^\]]+)\])?\)\s*\n\s*def\s+(\w+)'
        
        for match in re.finditer(pattern, content):
            path = match.group(1)
            methods = match.group(2)
            func_name = match.group(3)
            
            if methods:
                methods = sorted([m.strip().strip('"\'') for m in methods.split(',')])
            else:
                methods = ['GET']
            
            route_data = {
                'path': path,
                'methods': methods,
                'function': func_name,
            }
            
            # For /api/render route, extract form and files parameters
            if path == '/api/render' and func_name == 'render_api':
                params = _extract_render_api_params(content, func_name)
                route_data['form_keys'] = params['form_keys']
                route_data['files_keys'] = params['files_keys']
            
            routes.append(route_data)
    except Exception as e:
        routes.append({'error': f"Failed to parse routes: {e}"})
    
    return routes


def _extract_options_dict_keys(content: str, func_name: str = 'render_api') -> List[dict]:
    """
    Extract options dictionary keys and default values from render_api function.
    Returns a list of dicts with 'key' and 'default_value' fields.
    """
    options_items = []
    var_defaults = {}  # Cache for variable default values found earlier in function
    
    try:
        # Find the render_api function body
        func_start = content.find(f'def {func_name}(')
        if func_start == -1:
            return options_items
        
        # Find where the function ends (next def or end of significant block)
        func_end_match = re.search(r'\n\ndef\s+\w+\(|$', content[func_start + 100:])
        func_end = func_start + 100 + func_end_match.start() if func_end_match else len(content)
        func_body = content[func_start:func_end]
        
        # Extract variable assignments before options dict
        # Pattern: var_name = request.form.get("key", "default")
        var_pattern = r'(\w+)\s*=\s*request\.form\.get\(["\']([^"\']+)["\'],\s*([^)]+)\)'
        for var_match in re.finditer(var_pattern, func_body):
            var_name = var_match.group(1)
            default_str = var_match.group(3).strip()
            # Extract the default value (handle quotes)
            quoted_match = re.match(r'["\']([^"\']+)["\']', default_str)
            if quoted_match:
                var_defaults[var_name] = quoted_match.group(1)
            elif default_str in ('True', 'False', 'None', '0'):
                var_defaults[var_name] = default_str
        
        # Extract int() wrapped defaults (bloom_strength, etc.)
        int_pattern = r'(\w+)\s*=\s*int\(request\.form\.get\(["\']([^"\']+)["\'],\s*(\d+)\)\)'
        for int_match in re.finditer(int_pattern, func_body):
            var_name = int_match.group(1)
            default_val = int_match.group(3)
            var_defaults[var_name] = default_val
        
        # Special cases for computed variables
        var_defaults['style'] = 'fog'
        var_defaults['all_times_flag'] = 'false'
        var_defaults['use_sky_gradient'] = 'false'
        var_defaults['use_critic'] = 'True'  # Hardcoded
        var_defaults['sky_colors'] = 'None or tuple'  # Computed
        var_defaults['lighting_modes'] = '[lighting_mode] or [morning, noon, sunset, night]'  # Computed
        var_defaults['base_output_folder'] = 'OUTPUT_FOLDER or outdir'  # Computed
        var_defaults['outdir'] = '(empty string)'  # from .strip()
        var_defaults['sky_col1'] = '#2c3e50'
        var_defaults['sky_col2'] = '#e74c3c'
        var_defaults['cloud_type'] = 'na'
        
        # Find the options dictionary block
        options_start = func_body.find('options = {')
        if options_start == -1:
            return options_items
        
        # Find matching closing brace
        brace_count = 0
        in_string = False
        string_char = None
        escape_next = False
        options_content_start = options_start + len('options = {')
        
        for i in range(options_content_start, len(func_body)):
            char = func_body[i]
            if escape_next:
                escape_next = False
                continue
            if char == '\\':
                escape_next = True
                continue
            if not in_string and char in ('"', "'"):
                in_string = True
                string_char = char
            elif in_string and char == string_char:
                in_string = False
                string_char = None
                continue
            if not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    if brace_count == 0:
                        options_body = func_body[options_content_start:i]
                        break
                    brace_count -= 1
        
        # Process each line in the options dictionary
        for line in options_body.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Pattern to match: "key": value,  or  'key': value,
            key_value_match = re.match(r'["\']([^"\']+)["\']\s*:\s*(.+?)(?:,\s*$|,\s*#|$)', line)
            if not key_value_match:
                continue
            
            key = key_value_match.group(1)
            value_expr = key_value_match.group(2).strip().rstrip(',').rstrip()
            
            # Try to extract default value
            default_value = None
            
            # Case 1: request.form.get("key", "default") with .strip() or None
            if '.strip() or None' in value_expr:
                form_get_match = re.search(r'request\.form\.get\(["\']([^"\']+)["\'],\s*([^)]+)\)', value_expr)
                if form_get_match:
                    default_str = form_get_match.group(2).strip()
                    if default_str == '""' or default_str == "''":
                        default_value = 'None'
                    else:
                        quoted_match = re.match(r'["\']([^"\']+)["\']', default_str)
                        if quoted_match:
                            default_value = f"{quoted_match.group(1)} → None"
            # Case 1b: request.form.get("key", "default")
            elif 'request.form.get' in value_expr:
                form_get_full = r'request\.form\.get\(["\']([^"\']+)["\'],\s*([^)]+)\)'
                form_match = re.search(form_get_full, value_expr)
                if form_match:
                    default_str = form_match.group(2).strip()
                    # Extract quoted string default
                    quoted_match = re.match(r'["\']([^"\']+)["\']', default_str)
                    if quoted_match:
                        default_value = quoted_match.group(1)
                    elif default_str in ('True', 'False', 'None', '0'):
                        default_value = default_str
                    elif '.strip()' in default_str:
                        # Extract base value before .strip()
                        base_match = re.match(r'["\']([^"\']+)["\']', default_str)
                        if base_match:
                            default_value = base_match.group(1)
                        elif default_str == '""':
                            default_value = '(empty string)'
            else:
                # Case 2: Variable reference (check cache)
                var_name_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)$', value_expr)
                if var_name_match:
                    var_name = var_name_match.group(1)
                    if var_name in var_defaults:
                        default_value = var_defaults[var_name]
                    else:
                        default_value = f'({var_name})'  # Indicate it's a variable
                elif value_expr == 'None':
                    default_value = 'None'
                elif value_expr in ('True', 'False'):
                    default_value = value_expr
                else:
                    # Complex expression - show simplified version
                    if len(value_expr) > 50:
                        default_value = value_expr[:47] + "..."
                    else:
                        default_value = value_expr
            
            options_items.append({
                'key': key,
                'default_value': default_value or value_expr
            })
    
    except Exception as e:
        # Best effort - return empty on error
        pass
    
    return options_items


def extract_options_schema(app_file: Path) -> Optional[List[dict]]:
    """
    Extract the options dictionary schema from app.py render endpoint.
    Returns a list of dicts with 'key' and 'default_value' fields.
    """
    if not app_file.exists():
        return None
    
    try:
        content = app_file.read_text(encoding='utf-8', errors='replace')
        return _extract_options_dict_keys(content, 'render_api')
    except Exception as e:
        return None


def read_file_content(file_path: Path, project_root: Path, max_length: int = DEFAULT_MAX_FILE_LENGTH) -> tuple[str, bool]:
    """Read file content, truncating if necessary. Returns (content, was_truncated)."""
    if not file_path.exists():
        # Replace absolute path with placeholder
        rel_path = file_path.relative_to(project_root) if file_path.is_relative_to(project_root) else file_path.name
        return f"[FILE NOT FOUND: {rel_path}]", False
    
    try:
        content = file_path.read_text(encoding='utf-8', errors='replace')
        if len(content) > max_length:
            truncated_content = content[:max_length]
            return truncated_content + f"\n\n[TRUNCATED - Original file was {len(content)} characters, showing first {max_length} characters]", True
        return content, False
    except Exception as e:
        # Replace absolute path with placeholder
        rel_path = file_path.relative_to(project_root) if file_path.is_relative_to(project_root) else file_path.name
        return f"[ERROR READING FILE: {rel_path} - {e}]", False


def extract_html_js_excerpt(html_content: str) -> str:
    """
    Extract JavaScript code (inline script tags only) and key HTML elements (IDs referenced by JS)
    from templates/index.html for the snapshot.
    
    Returns a formatted excerpt containing:
    - All inline <script>...</script> blocks (excludes external scripts with src)
    - HTML elements with IDs referenced by JavaScript (renderBtn, dropzone, etc.)
    """
    import re
    output = []
    output.append("<!-- JavaScript Excerpt (inline script tags and key HTML elements) -->")
    output.append("")
    
    # Extract ONLY inline script tags (exclude external scripts with src attribute)
    # Pattern matches <script>...</script> but not <script src="...">
    script_pattern = r'<script(?![^>]*\ssrc=)[^>]*>(.*?)</script>'
    scripts = re.findall(script_pattern, html_content, re.DOTALL | re.IGNORECASE)
    
    if scripts:
        output.append("<!-- ========== Inline JavaScript Code ========== -->")
        output.append("")
        for i, script_content in enumerate(scripts, 1):
            # Wrap in script tags for readability
            output.append(f"<!-- Inline script block {i} -->")
            output.append("<script>")
            output.append(script_content.strip())
            output.append("</script>")
            output.append("")
    
    # Key IDs that are referenced in JavaScript (prioritize those used by API handlers)
    # These are the most critical for understanding the API integration
    key_ids = [
        # Core render/stream controls
        'renderBtn', 'previewBtn', 'progressContainer', 'progressBar', 'status-console',
        # File handling
        'dropzone', 'fileInput', 'selectedPreview', 'renderPreview',
        # Mashup controls
        'mashupBtn', 'mashupStatus', 'mashupPreview', 'mashupResolution', 'mashupCost',
        # Location/map
        'mapModal', 'openMapBtn', 'confirmLocBtn', 'location',
        # Advanced options
        'use_sky_gradient', 'sky_col1', 'sky_col2', 'advanced_toggle', 'advanced_container',
        'facade_gradient', 'facade_container',
        # Cost tracking
        'cost-period', 'costs-container', 'estimate',
        # Batch queue
        'batch-queue', 'queue-items', 'pause-queue-btn', 'resume-queue-btn'
    ]
    
    output.append("<!-- ========== Key HTML Elements (IDs referenced in JS) ========== -->")
    output.append("")
    
    # Extract elements with these IDs using a more robust approach
    # Sort IDs for deterministic output
    for element_id in sorted(key_ids):
        # Pattern to match opening tag with id attribute (handles various quote styles)
        id_pattern = rf'\bid=["\']?{re.escape(element_id)}["\']?'
        # Find the position of the id attribute
        matches = list(re.finditer(id_pattern, html_content, re.IGNORECASE))
        
        for match in matches:
            # Find the start of the tag (look backwards for <)
            start_pos = match.start()
            tag_start = html_content.rfind('<', 0, start_pos)
            if tag_start == -1:
                continue
            
            # Find the end of the opening tag
            tag_end = html_content.find('>', start_pos)
            if tag_end == -1:
                continue
            
            # Extract the tag name
            tag_match = re.match(r'<(\w+)', html_content[tag_start:tag_start+50])
            if not tag_match:
                continue
            
            tag_name = tag_match.group(1)
            opening_tag = html_content[tag_start:tag_end+1]
            
            # Check if it's a self-closing tag or void element
            if opening_tag.rstrip().endswith('/>') or tag_name.lower() in ['img', 'input', 'br', 'hr', 'meta', 'link', 'area', 'base', 'col', 'embed', 'source', 'track', 'wbr']:
                output.append(f"<!-- Element with id='{element_id}' -->")
                output.append(opening_tag)
                output.append("")
            else:
                # Find the matching closing tag
                remaining = html_content[tag_end+1:]
                closing_pattern = rf'</{re.escape(tag_name)}>'
                closing_match = re.search(closing_pattern, remaining, re.IGNORECASE)
                
                if closing_match:
                    # Include the full element including closing tag
                    closing_end = tag_end + 1 + closing_match.end()
                    full_element = html_content[tag_start:closing_end]
                    output.append(f"<!-- Element with id='{element_id}' -->")
                    output.append(full_element)
                    output.append("")
                else:
                    # Single line element (fallback)
                    output.append(f"<!-- Element with id='{element_id}' -->")
                    output.append(opening_tag)
                    output.append("")
            break  # Only take first match per ID
    
    return '\n'.join(output)


def redact_env_file(file_path: Path) -> str:
    """Read .env file and redact values, keeping keys."""
    if not file_path.exists():
        return "[.env file not found]"
    
    try:
        content = file_path.read_text(encoding='utf-8', errors='replace')
        lines = []
        
        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                lines.append(line)
                continue
            
            # Match KEY=VALUE pattern
            if '=' in line:
                key = line.split('=', 1)[0].strip()
                lines.append(f"{key}=__REDACTED__")
            else:
                lines.append(line)
        
        return '\n'.join(lines)
    except Exception as e:
        return f"[ERROR READING .env FILE: {e}]"


def find_notes_todos(root: Path) -> List[str]:
    """Search for TODO/FIXME comments and notes in markdown files."""
    notes = []
    
    # Look for markdown files that might contain notes
    markdown_files = [
        root / "README.md",
        root / "FEATURES.md",
        root / "PERFORMANCE_OPTIMIZATION_PLAN.md",
        root / "RENDERING_SPEED_OPTIMIZATION_OPTIONS.md",
    ]
    
    for md_file in markdown_files:
        if md_file.exists():
            try:
                content = md_file.read_text(encoding='utf-8', errors='replace')
                # Extract first 500 chars as a summary
                summary = content[:500].replace('\n', ' ').strip()
                if summary:
                    notes.append(f"**{md_file.name}**: {summary}...")
            except Exception:
                pass
    
    # Search for TODO/FIXME in key Python files
    python_files = [root / "app.py", root / "run_agent.py", root / "main_agent.py"]
    
    for py_file in python_files:
        if py_file.exists():
            try:
                content = py_file.read_text(encoding='utf-8', errors='replace')
                for line_num, line in enumerate(content.split('\n'), 1):
                    if 'TODO' in line or 'FIXME' in line or 'NOTE' in line:
                        note = line.strip()
                        if len(note) > 100:
                            note = note[:100] + "..."
                        notes.append(f"**{py_file.name}:{line_num}**: {note}")
            except Exception:
                pass
    
    return notes[:20]  # Limit to 20 notes


def generate_snapshot(project_root: Path = DEFAULT_PROJECT_ROOT, max_file_length: int = DEFAULT_MAX_FILE_LENGTH) -> str:
    """Generate the complete project snapshot markdown."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    project_root_resolved = project_root.resolve()
    
    sections = []
    
    # === Title ===
    sections.append("# Project Snapshot")
    sections.append("")
    
    # === How to use this snapshot ===
    sections.append("## How to use this snapshot")
    sections.append("")
    sections.append("- **For UI changes:** paste the `templates/index.html (JS excerpt)` section")
    sections.append("- **For backend changes:** paste API Inventory + the relevant route excerpt")
    sections.append("- **For new controls:** paste Options Schema")
    sections.append("")
    
    # === Adding a new endpoint checklist ===
    sections.append(NEW_ENDPOINT_CHECKLIST.strip())
    sections.append("")
    
    # === Build Identity ===
    sections.append("## Build Identity")
    sections.append("")
    sections.append("**Generated (Timestamp):** " + timestamp)
    sections.append("**Source Path:** <REPO_ROOT>")
    sections.append("")
    
    # === Repo Tree ===
    sections.append("## Repo Tree")
    sections.append("")
    sections.append("```")
    tree_output = build_repo_tree(project_root, project_root)
    sections.append(tree_output)
    sections.append("```")
    sections.append("")
    sections.append("*Note: Excluded folders: .git, venv, .venv, node_modules, __pycache__, input, output, dist*")
    sections.append("*Note: Excluded extensions: .png, .jpg, .jpeg, .webp, .gif, .mp4, .mov, .zip*")
    sections.append("")
    
    # === API Inventory ===
    sections.append("## API Inventory")
    sections.append("")
    app_file = project_root / "app.py"
    routes = extract_api_routes(app_file)
    
    if routes:
        sections.append("### Flask Routes")
        sections.append("")
        sections.append("| Path | Methods | Function |")
        sections.append("|------|---------|----------|")
        
        # Sort routes by path for stable ordering
        routes_sorted = sorted(routes, key=lambda r: r.get('path', '') if 'path' in r else 'zzz')
        
        render_route = None
        for route in routes_sorted:
            if 'error' in route:
                sections.append(f"| ERROR | - | {route['error']} |")
            else:
                methods_str = ', '.join(route['methods'])
                sections.append(f"| `{route['path']}` | {methods_str} | `{route['function']}` |")
                # Capture /api/render route for detailed parameter extraction
                if route.get('path') == '/api/render':
                    render_route = route
        
        sections.append("")
        
        # Add detailed parameter list for /api/render route
        if render_route and ('form_keys' in render_route or 'files_keys' in render_route):
            sections.append("### /api/render Request Parameters")
            sections.append("")
            
            if render_route.get('files_keys'):
                sections.append("**File Uploads (`request.files.getlist()`):**")
                sections.append("")
                for key in render_route['files_keys']:
                    sections.append(f"- `{key}`")
                sections.append("")
            
            if render_route.get('form_keys'):
                sections.append("**Form Parameters (`request.form.get()`):**")
                sections.append("")
                for key in render_route['form_keys']:
                    sections.append(f"- `{key}`")
                sections.append("")
    else:
        sections.append("*No routes found or error parsing app.py*")
        sections.append("")
    
    # === Job Streaming Protocol ===
    sections.append("## Job Streaming Protocol")
    sections.append("")
    sections.append("### Endpoint")
    sections.append("")
    sections.append("`GET /api/stream/<job_id>` - Server-Sent Events (SSE) endpoint for streaming job status updates.")
    sections.append("")
    sections.append("### Event Types")
    sections.append("")
    sections.append("Jobs emit three types of events via the queue:")
    sections.append("")
    sections.append("#### 1. Progress Events")
    sections.append("")
    sections.append("```json")
    sections.append('{"type": "progress", "message": "[filename.jpg | night] 🚀 Starting render..."}')
    sections.append("```")
    sections.append("")
    sections.append("**Client behavior**: Update status text/log, continue polling.")
    sections.append("")
    sections.append("#### 2. Complete Events")
    sections.append("")
    sections.append("Render job completion:")
    sections.append("```json")
    sections.append('{"type": "complete", "data": {"status": "success", "images": [...], "total_cost_usd": 0.20, "settings": {...}}}')
    sections.append("```")
    sections.append("")
    sections.append("Refine job completion:")
    sections.append("```json")
    sections.append('{"type": "complete", "data": {"status": "success", "image": "/output/path.jpg", "cost_usd": 0.05, "original_job_id": "..."}}')
    sections.append("```")
    sections.append("")
    sections.append("Inpaint job completion:")
    sections.append("```json")
    sections.append('{"type": "complete", "data": {"status": "success", "image": "/output/path.jpg", "cost_usd": 0.05}}')
    sections.append("```")
    sections.append("")
    sections.append("Preview job completion:")
    sections.append("```json")
    sections.append('{"type": "complete", "data": {"status": "success", "preview_path": "/output/preview.jpg", "message": "Preview generated. Use this to decide if you want to generate full resolution."}}')
    sections.append("```")
    sections.append("")
    sections.append("**Client behavior**: Render results (images/data), stop polling/stream, close EventSource.")
    sections.append("")
    sections.append("#### 3. Error Events")
    sections.append("")
    sections.append("```json")
    sections.append('{"type": "error", "message": "Job failed: error description"}')
    sections.append("```")
    sections.append("")
    sections.append("**Client behavior**: Display error message, stop polling/stream, close EventSource.")
    sections.append("")
    sections.append("### Client Recipe (EventSource)")
    sections.append("")
    sections.append("```javascript")
    sections.append("const evtSource = new EventSource(`/api/stream/${jobId}`);")
    sections.append("")
    sections.append("evtSource.onmessage = function(e) {")
    sections.append("  // Ignore keepalive comments")
    sections.append("  if (e.data === ': keepalive') return;")
    sections.append("  ")
    sections.append("  const msg = JSON.parse(e.data);")
    sections.append("  ")
    sections.append("  if (msg.type === 'progress') {")
    sections.append("    // Update UI with progress message")
    sections.append("    updateStatus(msg.message);")
    sections.append("  } else if (msg.type === 'complete') {")
    sections.append("    // Handle completion (render results, etc.)")
    sections.append("    handleCompletion(msg.data);")
    sections.append("    evtSource.close();  // Close stream")
    sections.append("  } else if (msg.type === 'error') {")
    sections.append("    // Handle error")
    sections.append("    showError(msg.message);")
    sections.append("    evtSource.close();  // Close stream")
    sections.append("  }")
    sections.append("};")
    sections.append("```")
    sections.append("")
    sections.append("### Notes")
    sections.append("")
    sections.append("- **Stream closure**: The stream closes automatically when a `complete` or `error` event is received (the `generate()` function breaks from the loop).")
    sections.append("- **Keepalive**: If no message arrives within 30 seconds, a keepalive comment (`: keepalive`) is sent to maintain the connection. The queue blocks for up to 30s waiting for messages.")
    sections.append("- **TTL expiration**: Jobs expire after 1 hour (3600 seconds). If a job expires, `JOBS.get(job_id)` returns `None`, and the stream sends an error message (`'Job not found or expired'`) and closes.")
    sections.append("")
    
    # === Static File Serving ===
    sections.append("## Static File Serving (Inputs/Outputs)")
    sections.append("")
    sections.append("### Routes")
    sections.append("")
    sections.append("| Route | Serves From | Purpose |")
    sections.append("|-------|-------------|---------|")
    sections.append("| `/input/<path:filename>` | `input/` (upload folder) | Original uploaded images for before/after comparison slider |")
    sections.append("| `/output/<path:filename>` | `output/` (output folder) | Generated result images displayed in the UI |")
    sections.append("")
    sections.append("**Usage notes:**")
    sections.append("- `/input/` serves original uploaded images (stored in `UPLOAD_FOLDER`), used in comparison sliders.")
    sections.append("- `/output/` serves generated media (images, and future videos). The UI should treat this as the canonical public path for all generated content (stored in `OUTPUT_FOLDER`).")
    sections.append("")
    
    # === Options Schema ===
    sections.append("## Options Schema")
    sections.append("")
    options_schema = extract_options_schema(app_file)
    if options_schema:
        sections.append("### Render API Options Dictionary")
        sections.append("")
        sections.append("| Key | Default Value |")
        sections.append("|-----|---------------|")
        for item in options_schema:
            key = item.get('key', '')
            default = item.get('default_value', '')
            # Escape pipe characters in values for markdown table
            default = str(default).replace('|', '\\|')
            sections.append(f"| `{key}` | `{default}` |")
        sections.append("")
    else:
        sections.append("*Could not extract options schema from app.py*")
        sections.append("")
    
    # === Key Files ===
    sections.append("## Key Files (truncated)")
    sections.append("")
    
    for file_rel_path in KEY_FILES:
        file_path = project_root / file_rel_path
        
        if file_path.exists():
            if file_rel_path == '.env' or file_path.name == '.env':
                sections.append(f"### {file_rel_path}")
                sections.append("")
                content = redact_env_file(file_path)
                sections.append("```")
                sections.append(content)
                sections.append("```")
                sections.append("")
                sections.append("*Note: .env values have been redacted for security*")
                sections.append("")
            elif file_rel_path == 'templates/index.html':
                # Special handling for templates/index.html: extract JS and key HTML elements
                sections.append("### templates/index.html (JS excerpt)")
                sections.append("")
                try:
                    html_content = file_path.read_text(encoding='utf-8', errors='replace')
                    content = extract_html_js_excerpt(html_content)
                    # Cap at 30,000 chars as per requirement
                    if len(content) > 30000:
                        content = content[:30000] + f"\n\n[TRUNCATED - Excerpt was {len(content)} characters, showing first 30,000 characters]"
                    sections.append("```html")
                    sections.append(content)
                    sections.append("```")
                    sections.append("")
                except Exception as e:
                    sections.append(f"*Error extracting JS excerpt: {e}*")
                    sections.append("")
            else:
                sections.append(f"### {file_rel_path}")
                sections.append("")
                content, was_truncated = read_file_content(file_path, project_root, max_file_length)
                # Replace any absolute paths in content with <REPO_ROOT>
                project_root_str = str(project_root_resolved)
                content = content.replace(project_root_str, '<REPO_ROOT>')
                # Also handle forward slash version (Windows paths might appear with / in some contexts)
                content = content.replace(project_root_str.replace('\\', '/'), '<REPO_ROOT>')
                sections.append("```")
                
                # Determine code block language
                if file_path.suffix == '.py':
                    lang = 'python'
                elif file_path.suffix == '.yaml' or file_path.suffix == '.yml':
                    lang = 'yaml'
                elif file_path.suffix == '.json':
                    lang = 'json'
                elif file_path.suffix == '.html':
                    lang = 'html'
                elif file_path.suffix == '.txt':
                    lang = 'text'
                else:
                    lang = ''
                
                if lang:
                    sections.append(lang)
                sections.append(content)
                sections.append("```")
                sections.append("")
                
                if was_truncated:
                    sections.append("*Note: File content truncated to 12,000 characters*")
                    sections.append("")
        else:
            sections.append("*[File not found]*")
            sections.append("")
    
    # Check for .env file separately (it's not in KEY_FILES but should be included)
    env_file = project_root / ".env"
    if env_file.exists():
        sections.append("### .env")
        sections.append("")
        content = redact_env_file(env_file)
        sections.append("```")
        sections.append(content)
        sections.append("```")
        sections.append("")
        sections.append("*Note: .env values have been redacted for security*")
        sections.append("")
    
    # === Notes/TODO ===
    sections.append("## Notes / TODO")
    sections.append("")
    notes = find_notes_todos(project_root)
    
    if notes:
        for note in notes:
            sections.append(f"- {note}")
        sections.append("")
    else:
        sections.append("*No TODO/FIXME notes found*")
        sections.append("")
    
    return '\n'.join(sections)


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Generate a project snapshot markdown file from the repository",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--out',
        type=str,
        default=str(DEFAULT_OUTPUT_FILE),
        help=f'Output file path (default: {DEFAULT_OUTPUT_FILE})'
    )
    parser.add_argument(
        '--max-chars',
        type=int,
        default=DEFAULT_MAX_FILE_LENGTH,
        help=f'Maximum characters per file before truncation (default: {DEFAULT_MAX_FILE_LENGTH})'
    )
    parser.add_argument(
        '--root',
        type=str,
        default=str(DEFAULT_PROJECT_ROOT),
        help=f'Project root directory (default: {DEFAULT_PROJECT_ROOT})'
    )
    
    args = parser.parse_args()
    
    # Convert string paths to Path objects
    project_root = Path(args.root).resolve()
    output_file = Path(args.out).resolve()
    max_file_length = args.max_chars
    
    # Validate project root exists
    if not project_root.exists():
        print(f"[ERROR] Project root does not exist: {project_root}", file=sys.stderr)
        sys.exit(1)
    
    if not project_root.is_dir():
        print(f"[ERROR] Project root is not a directory: {project_root}", file=sys.stderr)
        sys.exit(1)
    
    print("=" * 80)
    print("AI Lighting Agent - Project Snapshot Export")
    print("=" * 80)
    print()
    print(f"Project root: {project_root}")
    print(f"Output file: {output_file}")
    print(f"Max file length: {max_file_length:,} characters")
    print()
    
    try:
        snapshot_content = generate_snapshot(project_root, max_file_length)
        output_file.write_text(snapshot_content, encoding='utf-8')
        print(f"[OK] Snapshot written to: {output_file}")
        print()
        print("Snapshot includes:")
        print("  - Build Identity (timestamp, path)")
        print("  - Repo Tree (structure)")
        print("  - API Inventory (Flask routes)")
        print("  - Job Streaming Protocol (SSE event schema)")
        print("  - Options Schema (render API options)")
        print(f"  - Key Files (truncated to {max_file_length:,} chars)")
        print("  - Notes/TODO (from code and docs)")
        print()
        print("=" * 80)
    except Exception as e:
        print(f"[ERROR] Failed to generate snapshot: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


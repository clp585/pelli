# Bundle Compilation Guide

This document explains how to create a distributable bundle of the AI Lighting Agent.

## Quick Start

Run the bundler script:

```powershell
# Option 1: Use the PowerShell wrapper (recommended)
.\bundle.ps1

# Option 2: Run Python script directly
python compile_bundle.py
```

The bundle will be created in `dist/LightingAgent_BUNDLE_<timestamp>/`

## What Gets Included

The bundler copies the following items:

### Python Entrypoints
- `app.py` - Main Flask web application
- `run_agent.py` - Agent execution script
- `main_agent.py` - Primary agent entry point
- `config_utils.py` - Configuration utilities

### Configuration Files
- `config.yaml` - Application configuration
- `requirements.txt` - Python dependencies
- `styles.json` - Style definitions

### Essential Folders
- `templates/` - Flask HTML templates (required for web UI)
- `agent_tools/` - Core Python package (required for imports)
- `docs/` - Documentation files

### Scripts & Documentation
- All `.md` files (markdown documentation)
- All `.ps1` files (PowerShell scripts)
- All `.bat` files (batch scripts)

## What Gets Excluded

The following items are **intentionally excluded** from bundles:

### Build Artifacts
- `dist/` - Bundle output directory (to avoid recursive copying)
- `__pycache__/` - Python bytecode cache
- `*.pyc`, `*.pyo`, `*.pyd` - Compiled Python files

### Development Environment
- `.git/` - Git repository data
- `venv/`, `.venv/` - Virtual environments
- `node_modules/` - Node.js dependencies

### Runtime Data
- `input/` - User input images (excluded by design)
- `output/` - Generated output images (excluded by design)
- `*.log` - Log files

### IDE Files
- `.vscode/`, `.idea/` - Editor configuration

## Security: Environment Files

**Important:** `.env` files are automatically redacted during bundling.

- All environment variable **values** are replaced with `__REDACTED__`
- Environment variable **keys** are preserved
- This ensures sensitive API keys and secrets are not included in bundles
- You must configure `.env` files separately on the target deployment

Example:
```
# Original .env
GEMINIAPIKEY=actual_secret_key_here

# Bundled .env (redacted)
GEMINIAPIKEY=__REDACTED__
```

## Output Location

Bundles are created in:
```
dist/LightingAgent_BUNDLE_YYYYMMDD_HHMMSS/
```

After running the bundler, the newest bundle path is displayed in the output.

## Validation

The bundler automatically validates critical assets before creating the bundle:

- **CRITICAL**: `templates/index.html` - Required for Flask web interface
- **CRITICAL**: `agent_tools/` folder - Required for Python imports
- **WARNING**: `.env` file - May be needed for runtime configuration
- **WARNING**: `config.yaml` - May be needed for application settings

Warnings are displayed if critical items are missing, which would make the bundle non-runnable.

## Bundle Manifest

Each bundle includes `BUNDLE_MANIFEST.txt` with:
- Creation timestamp
- List of all included files and folders
- Validation warnings (if any)
- Notes about the bundle contents

## Usage After Bundling

1. Copy the bundle folder to your target location
2. Install dependencies: `pip install -r requirements.txt`
3. Configure environment variables in `.env` (if needed)
4. Run the application: `python app.py`


# Development Workflow

## Install Git hooks

```bash
python scripts/install_git_hooks.py
```

Copies hook templates from `scripts/hooks/` to `.git/hooks/` and makes them active.

## What the pre-commit hook does

Generates and stages `PROJECT_SNAPSHOT.md`.

**Fail-soft by default**: If snapshot generation fails, prints a warning but allows the commit to proceed.

## CI Enforcement

CI enforces snapshot freshness on every push and PR. If CI fails with a snapshot error, run `python export_agent_snapshot.py --out PROJECT_SNAPSHOT.md`, commit the updated snapshot, and push again.

## Skip / strict modes

### Skip snapshot generation

```bash
SKIP_SNAPSHOT=1 git commit -m "wip"
```

Windows PowerShell:
```powershell
$env:SKIP_SNAPSHOT="1"; git commit -m "wip"; $env:SKIP_SNAPSHOT=$null
```

### Strict mode (block on failure)

```bash
STRICT_SNAPSHOT=1 git commit -m "must have snapshot"
```

Windows PowerShell:
```powershell
$env:STRICT_SNAPSHOT="1"; git commit -m "must have snapshot"; $env:STRICT_SNAPSHOT=$null
```

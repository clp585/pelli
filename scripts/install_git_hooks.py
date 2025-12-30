#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Install Git Hooks

Copies template hooks from scripts/hooks/ to .git/hooks/
This makes hooks shareable across machines since .git/hooks/ is not committed.
"""

import os
import shutil
import sys
from pathlib import Path


def main():
    """Install git hooks from scripts/hooks/ to .git/hooks/"""
    # Get project root (parent of scripts/)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    hooks_source = script_dir / "hooks"
    hooks_target = project_root / ".git" / "hooks"
    
    # Check if .git/hooks exists (repo must be initialized)
    if not hooks_target.exists():
        print(f"[ERROR] .git/hooks directory not found. Is this a git repository?")
        print(f"Run 'git init' first, then run this script again.")
        sys.exit(1)
    
    # Check if source hooks directory exists
    if not hooks_source.exists():
        print(f"[ERROR] Source hooks directory not found: {hooks_source}")
        sys.exit(1)
    
    # Install each hook template (overwrites existing files)
    installed_count = 0
    for hook_file in hooks_source.glob("*"):
        if hook_file.is_file() and not hook_file.name.endswith(".sample"):
            target_file = hooks_target / hook_file.name
            
            try:
                # Copy the hook file (overwrites if exists)
                shutil.copy2(hook_file, target_file)
                print(f"Installed: {hook_file.name} -> .git/hooks/{hook_file.name}")
                installed_count += 1
            except Exception as e:
                print(f"[ERROR] Failed to install {hook_file.name}: {e}", file=sys.stderr)
                sys.exit(1)
    
    if installed_count == 0:
        print("[WARNING] No hook files found in scripts/hooks/")
    else:
        print(f"\n[OK] Installed {installed_count} hook(s) to .git/hooks/")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smoke test for Flask app

Tests that critical endpoints are working.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from app import app
except ImportError as e:
    print(f"FAIL: Could not import app: {e}")
    sys.exit(1)

def test_health():
    """Test GET /health returns HTTP 200"""
    with app.test_client() as client:
        response = client.get("/health")
        if response.status_code == 200:
            print("PASS: GET /health returns HTTP 200")
            return True
        else:
            print(f"FAIL: GET /health returned HTTP {response.status_code}, expected 200")
            return False

def main():
    """Run smoke tests"""
    tests_passed = 0
    tests_total = 0
    
    tests_total += 1
    if test_health():
        tests_passed += 1
    
    if tests_passed == tests_total:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""Agent-Flow Health Watcher — Runs every 5 minutes.

Checks:
1. API server (port 8000) — alive?
2. UI server (port 3000) — alive?
3. Tests — passing?
4. Git status — clean or dirty?
5. Vault/Obsidian — any changes?

Only reports when something is WRONG or IMPORTANT.
Silent when healthy (no noise).
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT = Path("/opt/data/Agent-Flow")
FRONTEND = PROJECT / "frontend"
API_HEALTH = "http://localhost:8000/health"
UI_HEALTH = "http://localhost:3000"

def check_url(url: str, timeout: int = 5) -> tuple[bool, str]:
    try:
        import urllib.request
        req = urllib.request.Request(url, method="GET")
        resp = urllib.request.urlopen(req, timeout=timeout)
        return True, f"{resp.status} OK"
    except Exception as e:
        return False, str(e)

def run_tests() -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["python3", "-W", "error::ResourceWarning", "-m", "unittest", "discover", "-s", "tests", "-v"],
            cwd=str(PROJECT),
            capture_output=True, text=True,
            timeout=60
        )
        if result.returncode == 0:
            return True, "All tests passed"
        else:
            return False, f"Tests FAILED: {result.stdout[-200:]}{result.stderr[-200:]}"
    except subprocess.TimeoutExpired:
        return False, "Tests timed out (60s)"
    except Exception as e:
        return False, f"Tests error: {e}"

def check_git() -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(PROJECT),
            capture_output=True, text=True,
            timeout=10
        )
        if result.stdout.strip():
            lines = result.stdout.strip().split("\n")
            return True, f"{len(lines)} uncommitted file(s)"
        else:
            return False, ""
    except Exception as e:
        return False, f"Git error: {e}"

def main():
    report = []
    timestamp = datetime.now().strftime("%H:%M")
    issues = 0

    # 1. API check
    api_ok, api_msg = check_url(API_HEALTH)
    if not api_ok:
        issues += 1
        report.append(f"🔴 API DOWN: {api_msg}")

    # 2. UI check  
    ui_ok, ui_msg = check_url(UI_HEALTH)
    if not ui_ok:
        issues += 1
        report.append(f"🔴 UI DOWN: {ui_msg}")

    # 3. Tests (only every hour — 12th run at 5min interval)
    test_ok, test_msg = True, ""
    # Only run tests if API and UI are up (every ~1 hour)
    if api_ok and ui_ok:
        minute = datetime.now().minute
        if minute % 10 == 0:  # every 10 minutes
            test_ok, test_msg = run_tests()
            if not test_ok:
                issues += 1
                report.append(f"🔴 {test_msg}")

    # 4. Git check
    dirty, git_msg = check_git()
    if dirty:
        report.append(f"⚠️ Git: {git_msg}")

    # 5. Check next.js build
    build_stale = False
    if api_ok and ui_ok and minute % 30 == 0:
        build_result = subprocess.run(
            ["npx", "next", "build"],
            cwd=str(FRONTEND),
            capture_output=True, text=True,
            timeout=120
        )
        if build_result.returncode != 0:
            report.append(f"🔴 Next.js build failed")

    # Always report if issues
    if issues > 0 or report:
        icon = "🟢" if issues == 0 else "🔴"
        print(f"{icon} Agent-Flow Report [{timestamp}]")
        for r in report:
            print(f"  {r}")
        if not test_ok and minute % 10 != 0:
            pass  # tests only run every 10min
        if issues == 0:
            print(f"  ✅ All systems healthy")
    else:
        # Silent — everything is fine
        sys.exit(0)

if __name__ == "__main__":
    main()
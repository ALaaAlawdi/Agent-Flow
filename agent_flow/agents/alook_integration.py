"""Alook integration for Agent-Flow.

Alook is an orchestration layer for AI workforces.
This module makes Agent-Flow export its org chart and runtime status
in a way that is ready to connect to Alook locally.
"""

from __future__ import annotations

import json
import socket
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter

from agent_flow.agents.agent_brain import WORKERS

router = APIRouter(prefix="/alook", tags=["alook"])

EXPORT_DIR = Path("/opt/data/Agent-Flow/.alook")
EXPORT_DIR.mkdir(exist_ok=True)
EXPORT_FILE = EXPORT_DIR / "agent_flow_company.json"


def _run(cmd: list[str]) -> tuple[int, str]:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
        output = (result.stdout or result.stderr or "").strip()
        return result.returncode, output
    except Exception as e:
        return 1, str(e)


def _http_ok(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=3) as r:
            return 200 <= r.status < 500
    except Exception:
        return False


def _port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except Exception:
        return False


def _build_company_export() -> dict:
    agents = []
    for worker_id, worker in WORKERS.items():
        agents.append(
            {
                "id": worker_id,
                "name": worker["name"],
                "role": worker["role"],
                "specialty": worker["specialty"],
                "tools": worker.get("tools", []),
                "reports_to": "founder" if worker_id != "founder" else None,
                "can_collaborate_with": worker.get("can_ask", []),
            }
        )

    return {
        "company": {
            "name": "Agent-Flow",
            "tagline": "AI company operating system staffed by agents",
            "source": "Agent-Flow",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "alook_ready": True,
        },
        "org_chart": agents,
        "runtime": {
            "brain_agents": len(WORKERS),
            "provider_neutral": True,
            "local_first": True,
            "recommended_entrypoints": [
                "Founder",
                "Researcher",
                "Reviewer",
                "Red Team",
                "Archivist",
            ],
        },
    }


@router.get("/status")
async def alook_status():
    """Check Alook CLI and local runtime status."""
    code, version = _run(["npx", "-y", "@alook/app", "--version"])
    return {
        "cli_available": code == 0,
        "cli_version": version if code == 0 else None,
        "web_running": _port_open("127.0.0.1", 15210),
        "email_worker_running": _port_open("127.0.0.1", 15211),
        "ws_worker_running": _port_open("127.0.0.1", 15212),
        "web_http_ready": _http_ok("http://localhost:15210"),
        "export_file": str(EXPORT_FILE),
        "export_exists": EXPORT_FILE.exists(),
        "brain_agents": len(WORKERS),
        "constitution_coverage": "10/10" if len(WORKERS) >= 10 else f"{len(WORKERS)}/10",
        "note": "onboard failed during migrations, but local services may still be startable if the DB was already initialized",
    }


@router.post("/export")
async def alook_export():
    """Export Agent-Flow org chart in Alook-ready JSON."""
    payload = _build_company_export()
    EXPORT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    return {
        "status": "exported",
        "path": str(EXPORT_FILE),
        "agents": len(payload["org_chart"]),
        "company": payload["company"]["name"],
    }


@router.get("/org")
async def alook_org():
    """Return the current Agent-Flow org chart for Alook."""
    return _build_company_export()


@router.post("/bootstrap")
async def alook_bootstrap():
    """Try to start local Alook in skip-register mode."""
    code, output = _run(["npx", "-y", "@alook/app", "onboard", "--skip-register"])
    return {
        "success": code == 0,
        "command": "npx -y @alook/app onboard --skip-register",
        "output": output[-1500:],
    }

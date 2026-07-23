"""Deterministic company-runtime API for missions, task boards, and event ledger."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agent_flow.runtime import CompanyRuntime

router = APIRouter(tags=["company"])


class CreateMissionRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    brief: str = Field(min_length=1, max_length=4000)
    budget: int = Field(gt=0, le=10_000)
    risk: Literal["low", "medium", "high", "critical"]


DEFAULT_DB_PATH = Path(".agent-flow/company.db")


def _runtime() -> CompanyRuntime:
    db_path = Path(os.getenv("AGENT_FLOW_DB", str(DEFAULT_DB_PATH)))
    capability_secret = os.getenv("AGENT_FLOW_CAPABILITY_SECRET")
    runtime = CompanyRuntime(
        db_path,
        capability_secret=capability_secret.encode("utf-8") if capability_secret else None,
    )
    runtime.bootstrap()
    return runtime


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, KeyError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=403, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, RuntimeError):
        return HTTPException(status_code=409, detail=str(exc))
    return HTTPException(status_code=500, detail="unexpected company runtime error")


@router.get("/missions")
def list_missions() -> dict:
    runtime = _runtime()
    return {"missions": runtime.list_missions()}


@router.post("/missions")
def create_mission(payload: CreateMissionRequest) -> dict:
    runtime = _runtime()
    try:
        mission_id = runtime.create_mission(
            title=payload.title,
            brief=payload.brief,
            budget=payload.budget,
            risk=payload.risk,
        )
    except Exception as exc:  # pragma: no cover - consolidated mapping
        raise _http_error(exc) from exc
    return {"mission_id": mission_id, "mission": runtime.mission(mission_id)}


@router.get("/missions/{mission_id}")
def mission_detail(mission_id: str) -> dict:
    runtime = _runtime()
    try:
        return runtime.mission(mission_id)
    except Exception as exc:  # pragma: no cover - consolidated mapping
        raise _http_error(exc) from exc


@router.post("/missions/{mission_id}/form-squad")
def form_squad(mission_id: str) -> dict:
    runtime = _runtime()
    try:
        assignments = runtime.form_squad(mission_id)
    except Exception as exc:  # pragma: no cover - consolidated mapping
        raise _http_error(exc) from exc
    return {"mission_id": mission_id, "assignments": assignments, "mission": runtime.mission(mission_id)}


@router.get("/missions/{mission_id}/packets")
def mission_packets(mission_id: str) -> dict:
    runtime = _runtime()
    try:
        packets = runtime.ready_task_packets(mission_id)
    except Exception as exc:  # pragma: no cover - consolidated mapping
        raise _http_error(exc) from exc
    return {"mission_id": mission_id, "packets": packets}


@router.get("/company/events")
def company_events() -> dict:
    runtime = _runtime()
    return {"events": runtime.events()}

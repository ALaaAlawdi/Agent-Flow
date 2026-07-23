from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import re
import sqlite3
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterator

from .domain import VALID_RISKS, VENTURE_WORKFLOW


DEFAULT_AGENTS = (
    ("founder", "Venture Founder", ("strategy", "capital", "integration")),
    ("oracle", "Market Intelligence", ("research", "forecasting", "evidence")),
    ("anthropologist", "Customer Anthropologist", ("discovery", "customer", "evidence")),
    ("architect", "Systems Architect", ("architecture", "security", "integration")),
    ("inventor", "Prototype Inventor", ("prototype", "experimentation", "delivery")),
    ("skeptic", "Independent Skeptic", ("verification", "falsification", "evidence")),
    ("redteam", "Adversarial Red Team", ("security", "red_team", "falsification")),
    ("economist", "Venture Economist", ("economics", "capital", "forecasting")),
    ("governor", "Constitutional Governor", ("governance", "policy", "approval")),
    ("archivist", "Organizational Archivist", ("learning", "evidence", "memory")),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class CompanyRuntime:
    def __init__(
        self,
        db_path: str | Path,
        *,
        capability_secret: bytes | None = None,
        capability_ttl_seconds: int = 300,
        clock: Callable[[], float] = time.time,
    ):
        if capability_secret is not None and len(capability_secret) < 32:
            raise ValueError("capability secret must be at least 32 bytes")
        if not isinstance(capability_ttl_seconds, int) or capability_ttl_seconds <= 0:
            raise ValueError("capability TTL must be a positive integer")
        self.db_path = Path(db_path)
        self._capability_secret = capability_secret
        self._capability_ttl_seconds = capability_ttl_seconds
        self._clock = clock

    @staticmethod
    def _encode_token_part(value: bytes) -> str:
        return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")

    @staticmethod
    def _decode_token_part(value: str) -> bytes:
        if not value or re.fullmatch(r"[A-Za-z0-9_-]+", value) is None:
            raise ValueError("invalid token segment")
        padded = value + "=" * (-len(value) % 4)
        decoded = base64.b64decode(padded.encode("ascii"), altchars=b"-_", validate=True)
        if CompanyRuntime._encode_token_part(decoded) != value:
            raise ValueError("non-canonical token segment")
        return decoded

    def _issue_task_capability(self, mission_id: str, task_id: str, worker_id: str) -> str:
        if self._capability_secret is None:
            raise RuntimeError("capability secret is required to issue external worker packets")
        now = int(self._clock())
        claims = {
            "exp": now + self._capability_ttl_seconds,
            "iat": now,
            "mission_id": mission_id,
            "nonce": uuid.uuid4().hex,
            "task_id": task_id,
            "worker_id": worker_id,
        }
        payload = json.dumps(claims, separators=(",", ":"), sort_keys=True).encode("utf-8")
        signature = hmac.new(self._capability_secret, payload, hashlib.sha256).digest()
        return f"{self._encode_token_part(payload)}.{self._encode_token_part(signature)}"

    def _authenticate_task_capability(self, token: str, mission_id: str, task_id: str) -> str:
        if self._capability_secret is None:
            raise RuntimeError("capability secret is required to authenticate external workers")
        if not isinstance(token, str) or len(token) > 4096:
            raise PermissionError("invalid task capability token")
        try:
            payload_part, signature_part = token.split(".")
            payload = self._decode_token_part(payload_part)
            supplied_signature = self._decode_token_part(signature_part)
        except (binascii.Error, ValueError, UnicodeEncodeError) as error:
            raise PermissionError("invalid task capability token") from error
        if len(payload) > 2048 or len(supplied_signature) != hashlib.sha256().digest_size:
            raise PermissionError("invalid task capability token")
        expected_signature = hmac.new(self._capability_secret, payload, hashlib.sha256).digest()
        if not hmac.compare_digest(supplied_signature, expected_signature):
            raise PermissionError("invalid task capability token")
        try:
            claims = json.loads(payload)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise PermissionError("invalid task capability token") from error
        if not isinstance(claims, dict):
            raise PermissionError("invalid task capability token")
        required_claims = {"exp", "iat", "mission_id", "nonce", "task_id", "worker_id"}
        if set(claims) != required_claims:
            raise PermissionError("invalid task capability token")
        if any(
            type(claims[name]) is not str or not claims[name]
            for name in ("mission_id", "task_id", "worker_id")
        ):
            raise PermissionError("invalid task capability token")
        issued_at = claims["iat"]
        expires_at = claims["exp"]
        nonce = claims["nonce"]
        if (
            type(issued_at) is not int
            or type(expires_at) is not int
            or type(nonce) is not str
            or re.fullmatch(r"[0-9a-f]{32}", nonce) is None
        ):
            raise PermissionError("invalid task capability token")
        if claims["mission_id"] != mission_id or claims["task_id"] != task_id:
            raise PermissionError("task capability token scope mismatch")
        now = self._clock()
        if (
            expires_at <= issued_at
            or expires_at - issued_at > self._capability_ttl_seconds
            or issued_at > now + 5
        ):
            raise PermissionError("invalid task capability token")
        if now >= expires_at:
            raise PermissionError("task capability token has expired")
        return claims["worker_id"]

    def complete_task_with_capability(
        self,
        mission_id: str,
        task_id: str,
        capability_token: str,
        evidence: dict,
    ) -> None:
        actor = self._authenticate_task_capability(capability_token, mission_id, task_id)
        self.complete_task(mission_id, task_id, actor, evidence)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def bootstrap(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS agents (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    capabilities TEXT NOT NULL,
                    reputation INTEGER NOT NULL DEFAULT 50,
                    available INTEGER NOT NULL DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    occurred_at TEXT NOT NULL,
                    type TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS missions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    brief TEXT NOT NULL,
                    risk TEXT NOT NULL,
                    status TEXT NOT NULL,
                    budget_total INTEGER NOT NULL,
                    budget_spent INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tasks (
                    mission_id TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    capability TEXT NOT NULL,
                    depends_on TEXT NOT NULL,
                    cost INTEGER NOT NULL,
                    independent_review INTEGER NOT NULL,
                    human_only INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    assigned_agent TEXT,
                    evidence TEXT,
                    PRIMARY KEY (mission_id, id),
                    FOREIGN KEY (mission_id) REFERENCES missions(id)
                );
                CREATE TABLE IF NOT EXISTS lessons (
                    id TEXT PRIMARY KEY,
                    mission_id TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    content TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (mission_id) REFERENCES missions(id)
                );
                """
            )
            existing = connection.execute("SELECT COUNT(*) FROM agents").fetchone()[0]
            if existing == 0:
                connection.executemany(
                    "INSERT INTO agents(id, title, capabilities) VALUES (?, ?, ?)",
                    [(agent_id, title, json.dumps(capabilities)) for agent_id, title, capabilities in DEFAULT_AGENTS],
                )
                connection.execute(
                    "INSERT INTO events(occurred_at, type, actor, payload) VALUES (?, ?, ?, ?)",
                    (utc_now(), "company_bootstrapped", "system", json.dumps({"agents": len(DEFAULT_AGENTS)})),
                )

    def _append_event(
        self,
        connection: sqlite3.Connection,
        event_type: str,
        actor: str,
        payload: dict,
    ) -> None:
        connection.execute(
            "INSERT INTO events(occurred_at, type, actor, payload) VALUES (?, ?, ?, ?)",
            (utc_now(), event_type, actor, json.dumps(payload, sort_keys=True)),
        )

    def create_mission(self, title: str, brief: str, budget: int, risk: str = "medium") -> str:
        if not title.strip() or not brief.strip():
            raise ValueError("title and brief are required")
        if budget <= 0:
            raise ValueError("budget must be positive")
        if risk not in VALID_RISKS:
            raise ValueError(f"risk must be one of: {', '.join(sorted(VALID_RISKS))}")
        mission_id = uuid.uuid4().hex[:12]
        created_at = utc_now()
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO missions
                   (id, title, brief, risk, status, budget_total, budget_spent, created_at)
                   VALUES (?, ?, ?, ?, 'active', ?, 0, ?)""",
                (mission_id, title.strip(), brief.strip(), risk, budget, created_at),
            )
            connection.executemany(
                """INSERT INTO tasks
                   (mission_id, position, id, title, capability, depends_on, cost,
                    independent_review, human_only, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    (
                        mission_id,
                        position,
                        spec.id,
                        spec.title,
                        spec.capability,
                        json.dumps(spec.depends_on),
                        spec.cost,
                        int(spec.independent_review),
                        int(spec.human_only),
                        "ready" if not spec.depends_on else "blocked",
                    )
                    for position, spec in enumerate(VENTURE_WORKFLOW)
                ],
            )
            self._append_event(
                connection,
                "mission_created",
                "founder",
                {"mission_id": mission_id, "budget": budget, "risk": risk, "title": title.strip()},
            )
        return mission_id

    def form_squad(self, mission_id: str) -> dict[str, str]:
        with self._connect() as connection:
            exists = connection.execute("SELECT 1 FROM missions WHERE id = ?", (mission_id,)).fetchone()
            if exists is None:
                raise KeyError(f"unknown mission: {mission_id}")
            agent_rows = connection.execute(
                "SELECT id, capabilities, reputation FROM agents WHERE available = 1 ORDER BY reputation DESC, id"
            ).fetchall()
            agents = [
                {"id": row["id"], "capabilities": json.loads(row["capabilities"]), "reputation": row["reputation"]}
                for row in agent_rows
            ]
            task_rows = connection.execute(
                "SELECT id, capability, depends_on, independent_review, human_only, assigned_agent "
                "FROM tasks WHERE mission_id = ? ORDER BY position",
                (mission_id,),
            ).fetchall()
            assignments: dict[str, str] = {}
            for task in task_rows:
                if task["human_only"]:
                    continue
                if task["assigned_agent"]:
                    assignments[task["id"]] = task["assigned_agent"]
                    continue
                excluded = {
                    assignments[dependency]
                    for dependency in json.loads(task["depends_on"])
                    if task["independent_review"] and dependency in assignments
                }
                eligible = [
                    agent
                    for agent in agents
                    if task["capability"] in agent["capabilities"] and agent["id"] not in excluded
                ]
                if not eligible:
                    raise RuntimeError(f"no eligible agent for task: {task['id']}")
                selected = eligible[0]["id"]
                connection.execute(
                    "UPDATE tasks SET assigned_agent = ? WHERE mission_id = ? AND id = ?",
                    (selected, mission_id, task["id"]),
                )
                assignments[task["id"]] = selected
            self._append_event(
                connection,
                "squad_formed",
                "system",
                {"mission_id": mission_id, "assignments": assignments},
            )
        return assignments

    def _promote_ready_tasks(self, connection: sqlite3.Connection, mission_id: str) -> None:
        rows = connection.execute(
            "SELECT id, depends_on, status FROM tasks WHERE mission_id = ? ORDER BY position",
            (mission_id,),
        ).fetchall()
        done = {row["id"] for row in rows if row["status"] == "done"}
        for row in rows:
            if row["status"] == "blocked" and all(
                dependency in done for dependency in json.loads(row["depends_on"])
            ):
                connection.execute(
                    "UPDATE tasks SET status = 'ready' WHERE mission_id = ? AND id = ?",
                    (mission_id, row["id"]),
                )

    def complete_task(self, mission_id: str, task_id: str, actor: str, evidence: dict) -> None:
        required_evidence = ("artifact", "verification", "summary")
        if not isinstance(evidence, dict) or any(
            not isinstance(evidence.get(field), str) or not evidence[field].strip()
            for field in required_evidence
        ):
            raise ValueError("evidence requires non-empty artifact, verification, and summary")
        with self._connect() as connection:
            mission = connection.execute(
                "SELECT budget_total, budget_spent, status FROM missions WHERE id = ?", (mission_id,)
            ).fetchone()
            if mission is None:
                raise KeyError(f"unknown mission: {mission_id}")
            if mission["status"] != "active":
                raise RuntimeError(f"mission is not active: {mission_id}")
            task = connection.execute(
                "SELECT * FROM tasks WHERE mission_id = ? AND id = ?", (mission_id, task_id)
            ).fetchone()
            if task is None:
                raise KeyError(f"unknown task: {task_id}")
            if task["human_only"]:
                raise PermissionError("human-only task must use human approval")
            if task["independent_review"]:
                allowed_decisions = {"build", "pivot", "kill"} if task_id == "board_review" else {
                    "pass",
                    "conditional",
                    "fail",
                }
                if evidence.get("decision") not in allowed_decisions:
                    raise ValueError(
                        f"{task_id} evidence requires decision in: {', '.join(sorted(allowed_decisions))}"
                    )
            if task["status"] != "ready":
                raise RuntimeError(f"task is not ready: {task_id}")
            if task["assigned_agent"] != actor:
                raise PermissionError(f"task is assigned to {task['assigned_agent']}")
            if mission["budget_spent"] + task["cost"] > mission["budget_total"]:
                raise RuntimeError("mission budget would be exceeded")
            connection.execute(
                "UPDATE tasks SET status = 'done', evidence = ? WHERE mission_id = ? AND id = ?",
                (json.dumps(evidence, sort_keys=True), mission_id, task_id),
            )
            connection.execute(
                "UPDATE missions SET budget_spent = budget_spent + ? WHERE id = ?",
                (task["cost"], mission_id),
            )
            connection.execute(
                "UPDATE agents SET reputation = MIN(100, reputation + 1) WHERE id = ?",
                (actor,),
            )
            self._promote_ready_tasks(connection, mission_id)
            self._append_event(
                connection,
                "task_completed",
                actor,
                {"mission_id": mission_id, "task_id": task_id, "cost": task["cost"], "evidence": evidence},
            )

    def approve_launch(self, mission_id: str, actor: str, actor_type: str, rationale: str) -> None:
        if actor_type != "human":
            raise PermissionError("launch approval requires a human actor")
        if not actor.strip():
            raise ValueError("human actor identity is required")
        if not rationale.strip():
            raise ValueError("approval rationale is required")
        with self._connect() as connection:
            mission = connection.execute("SELECT status FROM missions WHERE id = ?", (mission_id,)).fetchone()
            if mission is None:
                raise KeyError(f"unknown mission: {mission_id}")
            gate = connection.execute(
                "SELECT status FROM tasks WHERE mission_id = ? AND id = 'human_launch_approval'",
                (mission_id,),
            ).fetchone()
            if gate is None or gate["status"] != "ready":
                raise RuntimeError("human launch approval gate is not ready")
            reviews = connection.execute(
                """SELECT id, evidence FROM tasks
                   WHERE mission_id = ? AND independent_review = 1 AND human_only = 0""",
                (mission_id,),
            ).fetchall()
            decisions = {
                review["id"]: json.loads(review["evidence"] or "{}").get("decision")
                for review in reviews
            }
            blocking = sorted(
                task_id for task_id, decision in decisions.items()
                if task_id != "board_review" and decision == "fail"
            )
            if blocking:
                raise RuntimeError(f"blocking independent review: {', '.join(blocking)}")
            if decisions.get("board_review") != "build":
                raise RuntimeError("board decision must be build before launch approval")
            evidence = {
                "artifact": "human-approval-event",
                "verification": "local operator assertion",
                "summary": rationale.strip(),
            }
            connection.execute(
                """UPDATE tasks SET status = 'done', evidence = ?
                   WHERE mission_id = ? AND id = 'human_launch_approval'""",
                (json.dumps(evidence, sort_keys=True), mission_id),
            )
            connection.execute(
                "UPDATE missions SET status = 'approved_for_launch' WHERE id = ?", (mission_id,)
            )
            self._append_event(
                connection,
                "launch_approved",
                actor.strip(),
                {"mission_id": mission_id, "actor_type": "human", "rationale": rationale.strip()},
            )

    def record_lesson(self, mission_id: str, outcome: str, content: str, actor: str) -> str:
        valid_outcomes = {"build", "pivot", "kill", "incident"}
        if outcome not in valid_outcomes:
            raise ValueError(f"outcome must be one of: {', '.join(sorted(valid_outcomes))}")
        if not content.strip() or not actor.strip():
            raise ValueError("lesson content and actor are required")
        lesson_id = uuid.uuid4().hex[:12]
        with self._connect() as connection:
            board = connection.execute(
                "SELECT status, evidence FROM tasks WHERE mission_id = ? AND id = 'board_review'", (mission_id,)
            ).fetchone()
            if board is None:
                raise KeyError(f"unknown mission: {mission_id}")
            if board["status"] != "done":
                raise RuntimeError("board review must be complete before recording a lesson")
            board_decision = json.loads(board["evidence"] or "{}").get("decision")
            if outcome in {"build", "pivot", "kill"} and outcome != board_decision:
                raise RuntimeError(f"lesson outcome contradicts board decision: {board_decision}")
            connection.execute(
                """INSERT INTO lessons(id, mission_id, outcome, content, actor, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (lesson_id, mission_id, outcome, content.strip(), actor.strip(), utc_now()),
            )
            self._append_event(
                connection,
                "lesson_recorded",
                actor.strip(),
                {"lesson_id": lesson_id, "mission_id": mission_id, "outcome": outcome},
            )
        return lesson_id

    def lessons(self) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, mission_id, outcome, content, actor, created_at FROM lessons ORDER BY created_at, id"
            ).fetchall()
        return [dict(row) for row in rows]

    def ready_task_packets(self, mission_id: str, *, include_capability: bool = True) -> list[dict]:
        mission = self.mission(mission_id)
        tasks = {task["id"]: task for task in mission["tasks"]}
        packets = []
        for task in mission["tasks"]:
            if task["status"] != "ready" or task["human_only"]:
                continue
            if not task["assigned_agent"]:
                raise RuntimeError("form a squad before requesting task packets")
            input_artifacts = [
                tasks[dependency]["evidence"]["artifact"]
                for dependency in task["depends_on"]
                if tasks[dependency]["evidence"] is not None
            ]
            packets.append(
                {
                    "mission_id": mission_id,
                    "task_id": task["id"],
                    "worker_id": task["assigned_agent"],
                    "objective": task["title"],
                    "mission_context": {
                        "title": mission["title"],
                        "brief": mission["brief"],
                        "risk": mission["risk"],
                    },
                    "budget": {"credits": task["cost"]},
                    "input_artifacts": input_artifacts,
                    "allowed_tools": [],
                    "acceptance_criteria": [
                        "Return a retrievable artifact handle",
                        "Describe the verification actually performed",
                        "Separate evidence, assumptions, and recommendations",
                    ],
                    "evidence_contract": ["artifact", "verification", "summary"]
                    + (["decision"] if task["independent_review"] else []),
                    "decision_options": (
                        ["build", "pivot", "kill"]
                        if task["id"] == "board_review"
                        else ["pass", "conditional", "fail"]
                        if task["independent_review"]
                        else []
                    ),
                    "authority": {
                        "may_mutate_company_state": False,
                        "may_approve_own_work": False,
                        "may_trigger_external_side_effects": False,
                    },
                    **(
                        {
                            "capability_token": self._issue_task_capability(
                                mission_id, task["id"], task["assigned_agent"]
                            )
                        }
                        if include_capability and self._capability_secret is not None
                        else {}
                    ),
                }
            )
        return packets

    def mission(self, mission_id: str) -> dict:
        with self._connect() as connection:
            mission = connection.execute("SELECT * FROM missions WHERE id = ?", (mission_id,)).fetchone()
            if mission is None:
                raise KeyError(f"unknown mission: {mission_id}")
            tasks = connection.execute(
                "SELECT * FROM tasks WHERE mission_id = ? ORDER BY position", (mission_id,)
            ).fetchall()
        return {
            "id": mission["id"],
            "title": mission["title"],
            "brief": mission["brief"],
            "risk": mission["risk"],
            "status": mission["status"],
            "budget_total": mission["budget_total"],
            "budget_spent": mission["budget_spent"],
            "created_at": mission["created_at"],
            "tasks": [
                {
                    "id": task["id"],
                    "title": task["title"],
                    "capability": task["capability"],
                    "depends_on": json.loads(task["depends_on"]),
                    "cost": task["cost"],
                    "independent_review": bool(task["independent_review"]),
                    "human_only": bool(task["human_only"]),
                    "status": task["status"],
                    "assigned_agent": task["assigned_agent"],
                    "evidence": json.loads(task["evidence"]) if task["evidence"] else None,
                }
                for task in tasks
            ],
        }

    def list_missions(self) -> list[dict]:
        with self._connect() as connection:
            mission_rows = connection.execute(
                "SELECT * FROM missions ORDER BY created_at DESC, id DESC"
            ).fetchall()
            task_rows = connection.execute(
                "SELECT mission_id, status FROM tasks ORDER BY mission_id, position"
            ).fetchall()

        counts: dict[str, dict[str, int]] = {}
        for task in task_rows:
            mission_counts = counts.setdefault(task["mission_id"], {"blocked": 0, "ready": 0, "done": 0})
            if task["status"] in mission_counts:
                mission_counts[task["status"]] += 1

        missions = []
        for mission in mission_rows:
            missions.append(
                {
                    "id": mission["id"],
                    "title": mission["title"],
                    "brief": mission["brief"],
                    "risk": mission["risk"],
                    "status": mission["status"],
                    "budget_total": mission["budget_total"],
                    "budget_spent": mission["budget_spent"],
                    "created_at": mission["created_at"],
                    "task_counts": counts.get(mission["id"], {"blocked": 0, "ready": 0, "done": 0}),
                }
            )
        return missions

    def list_agents(self) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, title, capabilities, reputation, available FROM agents ORDER BY id"
            ).fetchall()
        return [
            {
                "id": row["id"],
                "title": row["title"],
                "capabilities": json.loads(row["capabilities"]),
                "reputation": row["reputation"],
                "available": bool(row["available"]),
            }
            for row in rows
        ]

    def events(self) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, occurred_at, type, actor, payload FROM events ORDER BY id"
            ).fetchall()
        return [
            {
                "id": row["id"],
                "occurred_at": row["occurred_at"],
                "type": row["type"],
                "actor": row["actor"],
                "payload": json.loads(row["payload"]),
            }
            for row in rows
        ]

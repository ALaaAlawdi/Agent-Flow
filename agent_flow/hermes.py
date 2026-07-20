"""Hermes Agent package adapter for bounded Agent-Flow workers."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Mapping


class HermesExecutionError(RuntimeError):
    """Raised when a Hermes worker cannot produce a valid evidence proposal."""


class HermesWorkerAdapter:
    """Run one Agent-Flow task through the Hermes ``--oneshot`` CLI contract."""

    _PROFILE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
    _APPROVED_TOOLSETS = frozenset({"web"})
    _PACKET_KEYS = (
        "mission_id",
        "task_id",
        "worker_id",
        "objective",
        "mission_context",
        "budget",
        "input_artifacts",
        "acceptance_criteria",
        "evidence_contract",
        "decision_options",
        "authority",
    )
    _MAX_PACKET_BYTES = 16_384
    _MAX_OUTPUT_BYTES = 16_384

    def __init__(
        self,
        *,
        profile: str,
        toolsets: tuple[str, ...] = ("web",),
        workdir: str | Path,
        executable: str = "hermes",
        timeout_seconds: int = 300,
        env: Mapping[str, str] | None = None,
    ) -> None:
        if self._PROFILE_PATTERN.fullmatch(profile) is None:
            raise ValueError("invalid Hermes profile name")
        if not toolsets or any(name not in self._APPROVED_TOOLSETS for name in toolsets):
            raise ValueError("Hermes toolsets must be approved read-only toolsets: web")
        path = Path(workdir).resolve()
        if not path.is_dir():
            raise ValueError("Hermes workdir must be an existing directory")
        if type(timeout_seconds) is not int or timeout_seconds <= 0:
            raise ValueError("Hermes timeout must be a positive integer")
        self.profile = profile
        self.toolsets = toolsets
        self.workdir = path
        self.executable = executable
        self.timeout_seconds = timeout_seconds
        self.env = dict(env) if env is not None else dict(os.environ)
        # The Hermes process needs provider credentials, but it must never inherit
        # Agent-Flow's state-transition signing authority.
        self.env.pop("AGENT_FLOW_CAPABILITY_SECRET", None)

    def _prompt(self, packet: Mapping[str, object]) -> str:
        public_packet = {key: packet[key] for key in self._PACKET_KEYS if key in packet}
        public_packet["enabled_toolsets"] = list(self.toolsets)
        encoded = json.dumps(public_packet, separators=(",", ":"), sort_keys=True)
        if len(encoded.encode("utf-8")) > self._MAX_PACKET_BYTES:
            raise ValueError("Hermes task packet exceeds the size limit")
        return (
            "You are an AI employee executing one bounded Agent-Flow company task. "
            "Use only the supplied task scope and your enabled tools. Do not change company state, "
            "approve launch, or invent authority. Return ONLY one JSON object with non-empty string "
            "keys artifact, verification, and summary. For an independent review, also include "
            "decision as pass, conditional, fail, build, pivot, or kill.\nTASK_PACKET="
            + encoded
        )

    def run_task(self, packet: Mapping[str, object]) -> dict[str, str]:
        prompt = self._prompt(packet)
        command = [
            self.executable,
            "-p",
            self.profile,
            "-z",
            prompt,
            "-t",
            ",".join(self.toolsets),
        ]
        try:
            completed = subprocess.run(
                command,
                cwd=self.workdir,
                env=self.env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout_seconds,
                check=False,
            )
        except FileNotFoundError as exc:
            raise HermesExecutionError(
                "Hermes executable not found; install hermes-agent and run hermes setup"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise HermesExecutionError("Hermes worker timed out") from exc
        if completed.returncode != 0:
            raise HermesExecutionError(f"Hermes worker exited with status {completed.returncode}")
        if len(completed.stdout.encode("utf-8")) > self._MAX_OUTPUT_BYTES:
            raise HermesExecutionError("Hermes worker output exceeds the size limit")
        try:
            evidence = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise HermesExecutionError("Hermes worker did not return valid JSON") from exc
        required = {"artifact", "verification", "summary"}
        allowed = required | {"decision"}
        if not isinstance(evidence, dict) or not required.issubset(evidence) or not set(evidence).issubset(allowed):
            raise HermesExecutionError("Hermes worker returned an invalid evidence schema")
        if any(not isinstance(value, str) or not value.strip() for value in evidence.values()):
            raise HermesExecutionError("Hermes evidence values must be non-empty strings")
        if "decision" in evidence and evidence["decision"] not in {
            "pass",
            "conditional",
            "fail",
            "build",
            "pivot",
            "kill",
        }:
            raise HermesExecutionError("Hermes worker returned an invalid decision")
        return evidence

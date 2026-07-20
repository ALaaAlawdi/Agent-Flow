"""Deterministic company constitution and venture workflow definitions."""

from __future__ import annotations

from dataclasses import dataclass


VALID_RISKS = {"low", "medium", "high", "critical"}


@dataclass(frozen=True)
class TaskSpec:
    id: str
    title: str
    capability: str
    depends_on: tuple[str, ...] = ()
    cost: int = 5
    independent_review: bool = False
    human_only: bool = False


VENTURE_WORKFLOW = (
    TaskSpec("mission_thesis", "Define the mission thesis and falsifiable claims", "strategy"),
    TaskSpec("market_intelligence", "Map alternatives, timing, and market evidence", "research"),
    TaskSpec("customer_pain", "Document costly customer pain and buyer evidence", "discovery"),
    TaskSpec("risk_hypothesis", "Identify existential, safety, and adoption risks", "red_team"),
    TaskSpec(
        "venture_design",
        "Synthesize a narrow venture design",
        "strategy",
        ("mission_thesis", "market_intelligence", "customer_pain", "risk_hypothesis"),
        8,
    ),
    TaskSpec("experiment_design", "Design the cheapest falsification experiment", "experimentation", ("venture_design",), 6),
    TaskSpec("architecture", "Design the product and operating architecture", "architecture", ("venture_design",), 8),
    TaskSpec("prototype", "Build and exercise the smallest credible prototype", "prototype", ("experiment_design", "architecture"), 20),
    TaskSpec("independent_verification", "Verify claims against evidence", "verification", ("prototype",), 8, True),
    TaskSpec("red_team", "Attack security, incentives, and failure recovery", "red_team", ("prototype",), 8, True),
    TaskSpec("economics_review", "Review willingness-to-pay and unit economics assumptions", "economics", ("prototype",), 6, True),
    TaskSpec(
        "board_review",
        "Issue a build, pivot, or kill recommendation",
        "governance",
        ("independent_verification", "red_team", "economics_review"),
        5,
        True,
    ),
    TaskSpec(
        "human_launch_approval",
        "Human authorization for external launch",
        "approval",
        ("board_review",),
        0,
        True,
        True,
    ),
)

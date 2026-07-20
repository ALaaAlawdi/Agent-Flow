"""Time Travel - Agents can revisit, replay, and branch their history.

Features:
- Snapshot timeline of all events
- Rewind to any point
- Branch into alternate timelines
- Compare outcomes across timelines
- Merge lessons from different timelines
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from collections import defaultdict


class TimelineSnapshot:
    """A snapshot of system state at a moment in time."""
    
    def __init__(self, snapshot_id: str, timestamp: str, state: dict):
        self.snapshot_id = snapshot_id
        self.timestamp = timestamp
        self.state = state
        self.label: Optional[str] = None
        self.parent_snapshot: Optional[str] = None
    
    def label_as(self, label: str):
        """Give this moment a name."""
        self.label = label
    
    def to_dict(self) -> dict:
        return {
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp,
            "label": self.label,
            "parent": self.parent_snapshot,
        }


class TimelineBranch:
    """An alternate timeline branch."""
    
    def __init__(self, branch_id: str, name: str, parent_snapshot: str):
        self.branch_id = branch_id
        self.name = name
        self.parent_snapshot = parent_snapshot
        self.snapshots: list[TimelineSnapshot] = []
        self.created_at = datetime.now().isoformat()
        self.outcomes: dict = {}


class TimeMachine:
    """Time travel system for agents.
    
    Features:
    - Save snapshots of any moment
    - Travel back to any snapshot
    - Branch into alternate realities
    - Compare outcomes across branches
    """
    
    def __init__(self):
        self.timeline: list[TimelineSnapshot] = []
        self.branches: dict[str, TimelineBranch] = {}
        self.active_branch: str = "main"
        self.bookmarks: dict[str, str] = {}  # name -> snapshot_id
    
    def snapshot(self, state: dict, label: Optional[str] = None) -> str:
        """Take a snapshot of current state."""
        snapshot_id = f"snap_{len(self.timeline)}_{int(datetime.now().timestamp())}"
        timestamp = datetime.now().isoformat()
        
        snap = TimelineSnapshot(snapshot_id, timestamp, state)
        if label:
            snap.label_as(label)
            self.bookmarks[label] = snapshot_id
        
        self.timeline.append(snap)
        return snapshot_id
    
    def bookmark(self, label: str) -> str:
        """Bookmark current moment."""
        if self.timeline:
            latest = self.timeline[-1]
            latest.label_as(label)
            self.bookmarks[label] = latest.snapshot_id
            return latest.snapshot_id
        return ""
    
    def travel_to(self, snapshot_id: str) -> Optional[dict]:
        """Travel back to a specific snapshot.
        
        Returns the state at that moment.
        """
        for snap in self.timeline:
            if snap.snapshot_id == snapshot_id:
                return snap.state
        
        # Check branches
        for branch in self.branches.values():
            for snap in branch.snapshots:
                if snap.snapshot_id == snapshot_id:
                    return snap.state
        
        return None
    
    def travel_to_bookmark(self, label: str) -> Optional[dict]:
        """Travel to a labeled moment."""
        snapshot_id = self.bookmarks.get(label)
        if snapshot_id:
            return self.travel_to(snapshot_id)
        return None
    
    def branch_from(
        self,
        snapshot_id: str,
        branch_name: str,
    ) -> str:
        """Branch off from a snapshot into an alternate timeline."""
        branch_id = f"branch_{len(self.branches)}_{int(datetime.now().timestamp())}"
        
        branch = TimelineBranch(branch_id, branch_name, snapshot_id)
        
        # Copy the parent snapshot to start
        for snap in self.timeline:
            if snap.snapshot_id == snapshot_id:
                new_snap = TimelineSnapshot(
                    f"{snap.snapshot_id}_b",
                    datetime.now().isoformat(),
                    dict(snap.state),  # Copy
                )
                new_snap.parent_snapshot = snap.snapshot_id
                branch.snapshots.append(new_snap)
                break
        
        self.branches[branch_id] = branch
        return branch_id
    
    def record_branch_outcome(self, branch_id: str, outcome: dict):
        """Record what happened in a branch."""
        if branch_id in self.branches:
            self.branches[branch_id].outcomes = outcome
    
    def compare_branches(self, branch_ids: list[str]) -> dict:
        """Compare outcomes across branches."""
        comparison = {
            "branches": {},
            "best": None,
            "worst": None,
        }
        
        scores = {}
        for bid in branch_ids:
            if bid in self.branches:
                branch = self.branches[bid]
                score = branch.outcomes.get("score", 0)
                comparison["branches"][bid] = {
                    "name": branch.name,
                    "score": score,
                    "outcomes": branch.outcomes,
                }
                scores[bid] = score
        
        if scores:
            comparison["best"] = max(scores.items(), key=lambda x: x[1])[0]
            comparison["worst"] = min(scores.items(), key=lambda x: x[1])[0]
        
        return comparison
    
    def merge_lessons(self, branch_ids: list[str]) -> list[str]:
        """Merge lessons learned from multiple timelines."""
        lessons = []
        
        for bid in branch_ids:
            if bid in self.branches:
                branch = self.branches[bid]
                # Extract insights from each branch
                if branch.outcomes.get("successes"):
                    for success in branch.outcomes["successes"]:
                        lessons.append(f"From {branch.name}: {success}")
                if branch.outcomes.get("failures"):
                    for failure in branch.outcomes["failures"]:
                        lessons.append(f"Avoid from {branch.name}: {failure}")
        
        return lessons
    
    def get_timeline(self) -> list[dict]:
        """Get the main timeline."""
        return [s.to_dict() for s in self.timeline]
    
    def get_bookmarks(self) -> dict[str, str]:
        """Get all bookmarks."""
        return dict(self.bookmarks)
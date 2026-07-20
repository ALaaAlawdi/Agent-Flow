"""Persistence Layer - Save and load agent state to disk.

Uses SQLite for simplicity. Stores:
- Teams
- Agents
- Interaction stream
- Conversations
- Memory
- Learning metrics
- Goals
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Any, Optional


class PersistenceManager:
    """Manages persistence of team state to disk."""
    
    def __init__(self, db_path: str = "agent_flow.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            
            # Teams
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS teams (
                    name TEXT PRIMARY KEY,
                    goal TEXT,
                    created_at TEXT,
                    metadata TEXT
                )
            """)
            
            # Interactions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS interactions (
                    interaction_id TEXT PRIMARY KEY,
                    team_name TEXT,
                    interaction_type TEXT,
                    source TEXT,
                    target TEXT,
                    data TEXT,
                    summary TEXT,
                    timestamp TEXT
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_interactions_team_time
                ON interactions(team_name, timestamp DESC)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_interactions_type
                ON interactions(team_name, interaction_type)
            """)
            
            # Conversations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    team_name TEXT,
                    participants TEXT,
                    topic TEXT,
                    started_at TEXT,
                    last_activity TEXT,
                    status TEXT,
                    messages TEXT
                )
            """)
            
            # Goals
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS goals (
                    goal_id TEXT PRIMARY KEY,
                    team_name TEXT,
                    goal TEXT,
                    outcome TEXT,
                    status TEXT,
                    created_at TEXT
                )
            """)
            
            conn.commit()
    
    def save_team(self, team_name: str, goal: str, metadata: dict = None):
        """Save team info."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO teams (name, goal, created_at, metadata)
                VALUES (?, ?, ?, ?)
            """, (
                team_name,
                goal,
                datetime.now().isoformat(),
                json.dumps(metadata or {}),
            ))
            conn.commit()
    
    def save_interaction(self, interaction: dict):
        """Save a single interaction."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO interactions
                (interaction_id, team_name, interaction_type, source, target, data, summary, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                interaction["interaction_id"],
                interaction.get("team_name", ""),
                interaction["type"],
                interaction.get("source"),
                interaction.get("target"),
                json.dumps(interaction.get("data", {})),
                interaction.get("summary", ""),
                interaction["timestamp"],
            ))
            conn.commit()
    
    def save_interactions_batch(self, team_name: str, interactions: list[dict]):
        """Save batch of interactions efficiently."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            data = []
            for i in interactions:
                data.append((
                    i["interaction_id"],
                    team_name,
                    i["type"],
                    i.get("source"),
                    i.get("target"),
                    json.dumps(i.get("data", {})),
                    i.get("summary", ""),
                    i["timestamp"],
                ))
            
            cursor.executemany("""
                INSERT OR REPLACE INTO interactions
                (interaction_id, team_name, interaction_type, source, target, data, summary, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, data)
            conn.commit()
    
    def load_interactions(
        self,
        team_name: str,
        limit: int = 100,
        interaction_type: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> list[dict]:
        """Load interactions from disk."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT interaction_id, interaction_type, source, target, data, summary, timestamp
                FROM interactions
                WHERE team_name = ?
            """
            params = [team_name]
            
            if interaction_type:
                query += " AND interaction_type = ?"
                params.append(interaction_type)
            
            if agent_id:
                query += " AND (source = ? OR target = ?)"
                params.extend([agent_id, agent_id])
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                interaction = {
                    "interaction_id": row[0],
                    "type": row[1],
                    "source": row[2],
                    "target": row[3],
                    "data": json.loads(row[4]) if row[4] else {},
                    "summary": row[5],
                    "timestamp": row[6],
                }
                results.append(interaction)
            
            return results
    
    def save_conversation(self, team_name: str, conversation: dict):
        """Save a conversation."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO conversations
                (conversation_id, team_name, participants, topic, started_at, last_activity, status, messages)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                conversation["conversation_id"],
                team_name,
                json.dumps(conversation.get("participants", [])),
                conversation.get("topic", ""),
                conversation.get("started_at", ""),
                conversation.get("last_activity", ""),
                conversation.get("status", "active"),
                json.dumps(conversation.get("messages", [])),
            ))
            conn.commit()
    
    def load_conversations(self, team_name: str, limit: int = 50) -> list[dict]:
        """Load conversations."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT conversation_id, participants, topic, started_at, last_activity, status, messages
                FROM conversations
                WHERE team_name = ?
                ORDER BY last_activity DESC
                LIMIT ?
            """, (team_name, limit))
            
            rows = cursor.fetchall()
            results = []
            for row in rows:
                results.append({
                    "conversation_id": row[0],
                    "participants": json.loads(row[1]) if row[1] else [],
                    "topic": row[2],
                    "started_at": row[3],
                    "last_activity": row[4],
                    "status": row[5],
                    "messages": json.loads(row[6]) if row[6] else [],
                })
            return results
    
    def get_team_stats(self, team_name: str) -> dict:
        """Get team statistics from DB."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            
            # Total interactions
            cursor.execute(
                "SELECT COUNT(*) FROM interactions WHERE team_name = ?",
                (team_name,)
            )
            total_interactions = cursor.fetchone()[0]
            
            # By type
            cursor.execute("""
                SELECT interaction_type, COUNT(*) as count
                FROM interactions
                WHERE team_name = ?
                GROUP BY interaction_type
                ORDER BY count DESC
            """, (team_name,))
            by_type = dict(cursor.fetchall())
            
            # By agent
            cursor.execute("""
                SELECT source, COUNT(*) as count
                FROM interactions
                WHERE team_name = ? AND source IS NOT NULL
                GROUP BY source
                ORDER BY count DESC
                LIMIT 10
            """, (team_name,))
            top_agents = dict(cursor.fetchall())
            
            return {
                "total_interactions": total_interactions,
                "by_type": by_type,
                "top_agents": top_agents,
            }
    
    def list_teams(self) -> list[dict]:
        """List all teams."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, goal, created_at FROM teams")
            rows = cursor.fetchall()
            return [
                {"name": r[0], "goal": r[1], "created_at": r[2]}
                for r in rows
            ]


class AutoPersistence:
    """Auto-save interactions as they happen.
    
    Subscribes to interaction stream and saves to DB.
    """
    
    def __init__(self, team_name: str, db_path: str = "agent_flow.db"):
        self.team_name = team_name
        self.db = PersistenceManager(db_path)
        self.buffer: list[dict] = []
        self.buffer_size = 50  # Save every N interactions
        
    def on_interaction(self, interaction: dict):
        """Callback for new interactions."""
        self.buffer.append(interaction)
        
        if len(self.buffer) >= self.buffer_size:
            self.flush()
    
    def flush(self):
        """Save buffered interactions to DB."""
        if self.buffer:
            self.db.save_interactions_batch(self.team_name, self.buffer)
            self.buffer.clear()
    
    def shutdown(self):
        """Save remaining interactions on shutdown."""
        self.flush()
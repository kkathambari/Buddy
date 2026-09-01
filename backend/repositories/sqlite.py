import sqlite3
import json
import os
import time
from typing import Any, Dict, Optional, List
from backend.repositories.base import BaseCompanionRepository, BaseMemoryRepository
from core.config import get_config
from core.logging import setup_logger

logger = setup_logger("sqlite_repository")

DB_PATH = "data/forge_companion.db"

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Profile table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profile (
        id TEXT PRIMARY KEY,
        name TEXT,
        role TEXT,
        language TEXT,
        goals TEXT
    )
    """)
    
    # 2. Relationship table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS relationship (
        companion_id TEXT PRIMARY KEY,
        bond INTEGER DEFAULT 0,
        trust REAL DEFAULT 0.5,
        respect REAL DEFAULT 0.5,
        confidence REAL DEFAULT 0.5,
        growth_stage TEXT DEFAULT 'month_1_careful',
        energy REAL DEFAULT 100.0,
        rarity TEXT DEFAULT 'common',
        alive INTEGER DEFAULT 1,
        is_first_run INTEGER DEFAULT 1
    )
    """)
    
    # 3. Timeline table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS timeline (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        companion_id TEXT,
        event_date TEXT,
        event TEXT,
        shared INTEGER DEFAULT 1,
        metadata TEXT
    )
    """)
    
    # 4. Learning table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS learning (
        topic TEXT PRIMARY KEY,
        confidence REAL DEFAULT 0.0,
        progress REAL DEFAULT 0.0,
        mastery REAL DEFAULT 0.0
    )
    """)
    
    # 5. Conversation table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversation (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        sender TEXT,
        message TEXT,
        timestamp REAL
    )
    """)
    
    # 6. Chat threads table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_threads (
        id TEXT PRIMARY KEY,
        companion_id TEXT,
        title TEXT,
        updated_at REAL
    )
    """)
    
    # Migrate existing conversations to default thread if not exists
    cursor.execute("SELECT DISTINCT session_id FROM conversation")
    for row in cursor.fetchall():
        sid = row["session_id"]
        cursor.execute("INSERT OR IGNORE INTO chat_threads (id, companion_id, title, updated_at) VALUES (?, ?, ?, ?)", 
                       (sid, sid, "Original Conversation", time.time()))

    # 7. Goals table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS goals (
        id TEXT PRIMARY KEY,
        companion_id TEXT,
        title TEXT,
        description TEXT,
        status TEXT,
        progress REAL DEFAULT 0.0,
        created_at REAL,
        updated_at REAL
    )
    """)

    conn.commit()
    conn.close()

# Initialize database schemas immediately on import
init_db()

class SqliteCompanionRepository(BaseCompanionRepository):
    """Concrete SQLite implementation for Companion soul data sync."""

    def get(self, id: str) -> Optional[Dict[str, Any]]:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Query relationship
            cursor.execute("SELECT * FROM relationship WHERE companion_id = ?", (id,))
            rel_row = cursor.fetchone()
            
            # Query profile
            cursor.execute("SELECT * FROM profile WHERE id = ?", (id,))
            prof_row = cursor.fetchone()
            
            conn.close()
            
            if not rel_row:
                return None
                
            stats = {
                "bond": rel_row["bond"],
                "trust": rel_row["trust"],
                "respect": rel_row["respect"],
                "confidence": rel_row["confidence"],
                "growth_stage": rel_row["growth_stage"]
            }
            
            # Construct companion soul response
            name = rel_row["name"] if "name" in rel_row.keys() else "Buddy"
            if prof_row and prof_row["name"]:
                name = prof_row["name"]
                
            soul = {
                "name": name,
                "energy": rel_row["energy"],
                "rarity": rel_row["rarity"],
                "alive": bool(rel_row["alive"]),
                "is_first_run": bool(rel_row["is_first_run"]),
                "stats": stats
            }
            return soul
        except Exception as e:
            logger.error(f"SqliteCompanionRepository get failed: {e}", exc_info=True)
            return None

    def save(self, id: str, data: Dict[str, Any]) -> bool:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            stats = data.get("stats", {})
            bond = stats.get("bond", 0)
            trust = stats.get("trust", 0.5)
            respect = stats.get("respect", 0.5)
            confidence = stats.get("confidence", 0.5)
            growth_stage = stats.get("growth_stage", "month_1_careful")
            
            name = data.get("name", "Buddy")
            energy = data.get("energy", 100.0)
            rarity = data.get("rarity", "common")
            alive = 1 if data.get("alive", True) else 0
            is_first_run = 1 if data.get("is_first_run", True) else 0
            
            # Insert or replace into relationship
            cursor.execute("""
            INSERT OR REPLACE INTO relationship 
            (companion_id, bond, trust, respect, confidence, growth_stage, energy, rarity, alive, is_first_run)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (id, bond, trust, respect, confidence, growth_stage, energy, rarity, alive, is_first_run))
            
            # Insert or replace into profile
            cursor.execute("SELECT * FROM profile WHERE id = ?", (id,))
            prof_row = cursor.fetchone()
            if prof_row:
                cursor.execute("""
                UPDATE profile SET name = ? WHERE id = ?
                """, (name, id))
            else:
                cursor.execute("""
                INSERT INTO profile (id, name, role, language, goals)
                VALUES (?, ?, ?, ?, ?)
                """, (id, name, "", "", ""))
                
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"SqliteCompanionRepository save failed: {e}", exc_info=True)
            return False

    def delete(self, id: str) -> bool:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM relationship WHERE companion_id = ?", (id,))
            cursor.execute("DELETE FROM profile WHERE id = ?", (id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"SqliteCompanionRepository delete failed: {e}", exc_info=True)
            return False

    def get_stats(self, companion_id: str) -> Optional[Dict[str, Any]]:
        soul = self.get(companion_id)
        if soul:
            return soul.get("stats")
        return None

class SqliteMemoryRepository(BaseMemoryRepository):
    """Concrete SQLite implementation for Chat History (Memory Engine)."""

    def get(self, id: str) -> Optional[List[Dict[str, Any]]]:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
            SELECT sender, message, timestamp FROM conversation 
            WHERE session_id = ? 
            ORDER BY id ASC
            """, (id,))
            rows = cursor.fetchall()
            conn.close()
            
            return [{"sender": row["sender"], "message": row["message"]} for row in rows]
        except Exception as e:
            logger.error(f"SqliteMemoryRepository get failed: {e}", exc_info=True)
            return []

    def save(self, id: str, data: Any) -> bool:
        try:
            if not isinstance(data, list):
                return False
                
            conn = get_connection()
            cursor = conn.cursor()
            
            # Clear existing
            cursor.execute("DELETE FROM conversation WHERE session_id = ?", (id,))
            
            # Insert new list of messages
            for msg in data:
                sender = msg.get("sender", "")
                message = msg.get("message", "")
                timestamp = msg.get("timestamp", time.time())
                cursor.execute("""
                INSERT INTO conversation (session_id, sender, message, timestamp)
                VALUES (?, ?, ?, ?)
                """, (id, sender, message, timestamp))
                
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"SqliteMemoryRepository save failed: {e}", exc_info=True)
            return False

    def delete(self, id: str) -> bool:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM conversation WHERE session_id = ?", (id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"SqliteMemoryRepository delete failed: {e}", exc_info=True)
            return False

    def get_recent_history(self, session_id: str, limit: int = 20) -> list:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
            SELECT sender, message, timestamp FROM conversation 
            WHERE session_id = ? 
            ORDER BY id DESC LIMIT ?
            """, (session_id, limit))
            rows = cursor.fetchall()
            conn.close()
            
            # Reverse DESC to preserve chronological order
            history = [{"sender": row["sender"], "message": row["message"]} for row in reversed(rows)]
            return history
        except Exception as e:
            logger.error(f"SqliteMemoryRepository get_recent_history failed: {e}", exc_info=True)
            return []

    def get_threads(self, companion_id: str) -> list:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, title, updated_at FROM chat_threads 
            WHERE companion_id = ? 
            ORDER BY updated_at DESC
            """, (companion_id,))
            rows = cursor.fetchall()
            conn.close()
            return [{"id": row["id"], "title": row["title"], "updated_at": row["updated_at"]} for row in rows]
        except Exception as e:
            logger.error(f"SqliteMemoryRepository get_threads failed: {e}", exc_info=True)
            return []

    def create_thread(self, companion_id: str, title: str) -> str:
        try:
            import uuid
            thread_id = str(uuid.uuid4())
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO chat_threads (id, companion_id, title, updated_at)
            VALUES (?, ?, ?, ?)
            """, (thread_id, companion_id, title, time.time()))
            conn.commit()
            conn.close()
            return thread_id
        except Exception as e:
            logger.error(f"SqliteMemoryRepository create_thread failed: {e}", exc_info=True)
            return ""

class SqliteGoalRepository:
    def get_goals(self, companion_id: str) -> List[Dict[str, Any]]:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM goals WHERE companion_id = ? ORDER BY created_at DESC", (companion_id,))
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"SqliteGoalRepository get_goals failed: {e}", exc_info=True)
            return []

    def create_goal(self, data: Dict[str, Any]) -> str:
        try:
            import uuid
            goal_id = str(uuid.uuid4())
            conn = get_connection()
            cursor = conn.cursor()
            now = time.time()
            cursor.execute("""
            INSERT INTO goals (id, companion_id, title, description, status, progress, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (goal_id, data["companion_id"], data["title"], data.get("description", ""), data.get("status", "active"), data.get("progress", 0.0), now, now))
            conn.commit()
            conn.close()
            return goal_id
        except Exception as e:
            logger.error(f"SqliteGoalRepository create_goal failed: {e}", exc_info=True)
            return ""

    def update_goal(self, goal_id: str, companion_id: str, data: Dict[str, Any]) -> bool:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            updates = []
            values = []
            for k in ["title", "description", "status", "progress"]:
                if k in data:
                    updates.append(f"{k} = ?")
                    values.append(data[k])
            
            if not updates:
                return False
                
            updates.append("updated_at = ?")
            values.extend([time.time(), goal_id, companion_id])
            
            query = f"UPDATE goals SET {', '.join(updates)} WHERE id = ? AND companion_id = ?"
            cursor.execute(query, values)
            updated = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return updated
        except Exception as e:
            logger.error(f"SqliteGoalRepository update_goal failed: {e}", exc_info=True)
            return False

    def delete_goal(self, goal_id: str, companion_id: str) -> bool:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM goals WHERE id = ? AND companion_id = ?", (goal_id, companion_id))
            deleted = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return deleted
        except Exception as e:
            logger.error(f"SqliteGoalRepository delete_goal failed: {e}", exc_info=True)
            return False

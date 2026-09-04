import time
import json
import uuid
from typing import Any, Dict, Optional, List
from backend.db import SessionLocal, engine, Base
from backend.models import (
    Profile, Relationship, Conversation, ChatThread, 
    Goal, Plan, ScheduledTask
)
from backend.repositories.base import BaseCompanionRepository, BaseMemoryRepository
from core.logging import setup_logger
from sqlalchemy.orm import Session

logger = setup_logger("postgres_repository")

def init_db():
    Base.metadata.create_all(bind=engine)

class PostgresCompanionRepository(BaseCompanionRepository):
    """Concrete SQLAlchemy implementation for Companion soul data sync."""
    
    def get(self, id: str) -> Optional[Dict[str, Any]]:
        try:
            with SessionLocal() as db:
                rel = db.query(Relationship).filter(Relationship.companion_id == id).first()
                prof = db.query(Profile).filter(Profile.id == id).first()
                
                if not rel:
                    return None
                    
                stats = {
                    "bond": rel.bond,
                    "trust": rel.trust,
                    "respect": rel.respect,
                    "confidence": rel.confidence,
                    "growth_stage": rel.growth_stage
                }
                
                name = prof.name if prof and prof.name else "Buddy"
                
                soul = {
                    "name": name,
                    "energy": rel.energy,
                    "rarity": rel.rarity,
                    "alive": bool(rel.alive),
                    "is_first_run": bool(rel.is_first_run),
                    "stats": stats
                }
                return soul
        except Exception as e:
            logger.error(f"PostgresCompanionRepository get failed: {e}", exc_info=True)
            return None

    def save(self, id: str, data: Dict[str, Any]) -> bool:
        try:
            with SessionLocal() as db:
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
                
                rel = db.query(Relationship).filter(Relationship.companion_id == id).first()
                if rel:
                    rel.bond = bond
                    rel.trust = trust
                    rel.respect = respect
                    rel.confidence = confidence
                    rel.growth_stage = growth_stage
                    rel.energy = energy
                    rel.rarity = rarity
                    rel.alive = alive
                    rel.is_first_run = is_first_run
                else:
                    rel = Relationship(
                        companion_id=id, bond=bond, trust=trust, respect=respect,
                        confidence=confidence, growth_stage=growth_stage,
                        energy=energy, rarity=rarity, alive=alive, is_first_run=is_first_run
                    )
                    db.add(rel)
                
                prof = db.query(Profile).filter(Profile.id == id).first()
                if prof:
                    prof.name = name
                else:
                    prof = Profile(id=id, name=name, role="", language="", goals="")
                    db.add(prof)
                    
                db.commit()
                return True
        except Exception as e:
            logger.error(f"PostgresCompanionRepository save failed: {e}", exc_info=True)
            return False

    def delete(self, id: str) -> bool:
        try:
            with SessionLocal() as db:
                db.query(Relationship).filter(Relationship.companion_id == id).delete()
                db.query(Profile).filter(Profile.id == id).delete()
                db.commit()
                return True
        except Exception as e:
            logger.error(f"PostgresCompanionRepository delete failed: {e}", exc_info=True)
            return False

    def get_stats(self, companion_id: str) -> Optional[Dict[str, Any]]:
        soul = self.get(companion_id)
        if soul:
            return soul.get("stats")
        return None

class PostgresMemoryRepository(BaseMemoryRepository):
    """Concrete SQLAlchemy implementation for Chat History (Memory Engine)."""

    def get(self, id: str) -> Optional[List[Dict[str, Any]]]:
        try:
            with SessionLocal() as db:
                messages = db.query(Conversation).filter(Conversation.session_id == id).order_by(Conversation.id.asc()).all()
                return [{"sender": msg.sender, "message": msg.message} for msg in messages]
        except Exception as e:
            logger.error(f"PostgresMemoryRepository get failed: {e}", exc_info=True)
            return []

    def save(self, id: str, data: Any) -> bool:
        try:
            if not isinstance(data, list):
                return False
                
            with SessionLocal() as db:
                # Clear existing
                db.query(Conversation).filter(Conversation.session_id == id).delete()
                
                # Insert new list of messages
                for msg in data:
                    sender = msg.get("sender", "")
                    message = msg.get("message", "")
                    timestamp = msg.get("timestamp", time.time())
                    new_msg = Conversation(session_id=id, sender=sender, message=message, timestamp=timestamp)
                    db.add(new_msg)
                    
                db.commit()
                return True
        except Exception as e:
            logger.error(f"PostgresMemoryRepository save failed: {e}", exc_info=True)
            return False

    def delete(self, id: str) -> bool:
        try:
            with SessionLocal() as db:
                db.query(Conversation).filter(Conversation.session_id == id).delete()
                db.commit()
                return True
        except Exception as e:
            logger.error(f"PostgresMemoryRepository delete failed: {e}", exc_info=True)
            return False

    def get_recent_history(self, session_id: str, limit: int = 20) -> list:
        try:
            with SessionLocal() as db:
                messages = db.query(Conversation).filter(Conversation.session_id == session_id).order_by(Conversation.id.desc()).limit(limit).all()
                # Reverse DESC to preserve chronological order
                return [{"sender": msg.sender, "message": msg.message} for msg in reversed(messages)]
        except Exception as e:
            logger.error(f"PostgresMemoryRepository get_recent_history failed: {e}", exc_info=True)
            return []

    def get_threads(self, companion_id: str) -> list:
        try:
            with SessionLocal() as db:
                threads = db.query(ChatThread).filter(ChatThread.companion_id == companion_id).order_by(ChatThread.updated_at.desc()).all()
                return [{"id": t.id, "title": t.title, "updated_at": t.updated_at} for t in threads]
        except Exception as e:
            logger.error(f"PostgresMemoryRepository get_threads failed: {e}", exc_info=True)
            return []

    def create_thread(self, companion_id: str, title: str) -> str:
        try:
            thread_id = str(uuid.uuid4())
            with SessionLocal() as db:
                thread = ChatThread(id=thread_id, companion_id=companion_id, title=title, updated_at=time.time())
                db.add(thread)
                db.commit()
                return thread_id
        except Exception as e:
            logger.error(f"PostgresMemoryRepository create_thread failed: {e}", exc_info=True)
            return ""

class PostgresGoalRepository:
    def get_goals(self, companion_id: str) -> List[Dict[str, Any]]:
        try:
            with SessionLocal() as db:
                goals = db.query(Goal).filter(Goal.companion_id == companion_id).order_by(Goal.created_at.desc()).all()
                return [{
                    "id": g.id,
                    "companion_id": g.companion_id,
                    "title": g.title,
                    "description": g.description,
                    "status": g.status,
                    "progress": g.progress,
                    "created_at": g.created_at,
                    "updated_at": g.updated_at
                } for g in goals]
        except Exception as e:
            logger.error(f"PostgresGoalRepository get_goals failed: {e}", exc_info=True)
            return []

    def create_goal(self, data: Dict[str, Any]) -> str:
        try:
            goal_id = str(uuid.uuid4())
            with SessionLocal() as db:
                now = time.time()
                goal = Goal(
                    id=goal_id,
                    companion_id=data["companion_id"],
                    title=data["title"],
                    description=data.get("description", ""),
                    status=data.get("status", "active"),
                    progress=data.get("progress", 0.0),
                    created_at=now,
                    updated_at=now
                )
                db.add(goal)
                db.commit()
                return goal_id
        except Exception as e:
            logger.error(f"PostgresGoalRepository create_goal failed: {e}", exc_info=True)
            return ""

    def update_goal(self, goal_id: str, companion_id: str, data: Dict[str, Any]) -> bool:
        try:
            with SessionLocal() as db:
                goal = db.query(Goal).filter(Goal.id == goal_id, Goal.companion_id == companion_id).first()
                if not goal:
                    return False
                
                updated = False
                for k in ["title", "description", "status", "progress"]:
                    if k in data:
                        setattr(goal, k, data[k])
                        updated = True
                
                if updated:
                    goal.updated_at = time.time()
                    db.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"PostgresGoalRepository update_goal failed: {e}", exc_info=True)
            return False

    def delete_goal(self, goal_id: str, companion_id: str) -> bool:
        try:
            with SessionLocal() as db:
                deleted = db.query(Goal).filter(Goal.id == goal_id, Goal.companion_id == companion_id).delete()
                db.commit()
                return deleted > 0
        except Exception as e:
            logger.error(f"PostgresGoalRepository delete_goal failed: {e}", exc_info=True)
            return False

class PostgresPlannerRepository:
    def get_plan(self, companion_id: str) -> Optional[Dict[str, Any]]:
        try:
            with SessionLocal() as db:
                plan = db.query(Plan).filter(Plan.companion_id == companion_id).first()
                if plan:
                    return {
                        "goal": plan.goal,
                        "tasks": json.loads(plan.tasks),
                        "completed": bool(plan.completed)
                    }
                return None
        except Exception as e:
            logger.error(f"PostgresPlannerRepository get_plan failed: {e}", exc_info=True)
            return None

    def save_plan(self, companion_id: str, plan_data: Dict[str, Any]) -> bool:
        try:
            with SessionLocal() as db:
                plan = db.query(Plan).filter(Plan.companion_id == companion_id).first()
                goal = plan_data.get("goal", "")
                tasks_json = json.dumps(plan_data.get("tasks", []))
                completed = 1 if plan_data.get("completed", False) else 0
                now = time.time()
                
                if plan:
                    plan.goal = goal
                    plan.tasks = tasks_json
                    plan.completed = completed
                    plan.updated_at = now
                else:
                    plan = Plan(
                        companion_id=companion_id,
                        goal=goal,
                        tasks=tasks_json,
                        completed=completed,
                        updated_at=now
                    )
                    db.add(plan)
                db.commit()
                return True
        except Exception as e:
            logger.error(f"PostgresPlannerRepository save_plan failed: {e}", exc_info=True)
            return False

    def delete_plan(self, companion_id: str) -> bool:
        try:
            with SessionLocal() as db:
                db.query(Plan).filter(Plan.companion_id == companion_id).delete()
                db.commit()
                return True
        except Exception as e:
            logger.error(f"PostgresPlannerRepository delete_plan failed: {e}", exc_info=True)
            return False

class PostgresScheduleRepository:
    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        try:
            now = time.time()
            with SessionLocal() as db:
                tasks = db.query(ScheduledTask).filter(
                    ScheduledTask.status == 'pending',
                    ScheduledTask.run_at <= now
                ).all()
                return [{
                    "id": t.id,
                    "companion_id": t.companion_id,
                    "name": t.name,
                    "prompt": t.prompt,
                    "run_at": t.run_at,
                    "recurring": bool(t.recurring),
                    "interval_sec": t.interval_sec,
                    "status": t.status
                } for t in tasks]
        except Exception as e:
            logger.error(f"PostgresScheduleRepository get_pending_tasks failed: {e}", exc_info=True)
            return []

    def create_task(self, task_data: Dict[str, Any]) -> str:
        try:
            task_id = str(uuid.uuid4())
            with SessionLocal() as db:
                task = ScheduledTask(
                    id=task_id,
                    companion_id=task_data["companion_id"],
                    name=task_data["name"],
                    prompt=task_data["prompt"],
                    run_at=task_data["run_at"],
                    recurring=1 if task_data.get("recurring") else 0,
                    interval_sec=task_data.get("interval_sec", 0.0),
                    status="pending"
                )
                db.add(task)
                db.commit()
                return task_id
        except Exception as e:
            logger.error(f"PostgresScheduleRepository create_task failed: {e}", exc_info=True)
            return ""

    def mark_completed(self, task_id: str, reschedule_at: Optional[float] = None) -> bool:
        try:
            with SessionLocal() as db:
                task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
                if not task:
                    return False
                
                if reschedule_at is not None:
                    task.run_at = reschedule_at
                    task.status = 'pending'
                else:
                    task.status = 'completed'
                db.commit()
                return True
        except Exception as e:
            logger.error(f"PostgresScheduleRepository mark_completed failed: {e}", exc_info=True)
            return False

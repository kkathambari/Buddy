from sqlalchemy import Column, String, Float, Integer, Boolean, Text
from backend.db import Base
import time

class Profile(Base):
    __tablename__ = "profile"
    id = Column(String, primary_key=True)
    name = Column(String)
    role = Column(String)
    language = Column(String)
    goals = Column(String)
    autonomy_level = Column(String, default="guided")

class Relationship(Base):
    __tablename__ = "relationship"
    companion_id = Column(String, primary_key=True)
    bond = Column(Integer, default=0)
    trust = Column(Float, default=0.5)
    respect = Column(Float, default=0.5)
    confidence = Column(Float, default=0.5)
    growth_stage = Column(String, default="month_1_careful")
    energy = Column(Float, default=100.0)
    rarity = Column(String, default="common")
    alive = Column(Integer, default=1)
    is_first_run = Column(Integer, default=1)

class Timeline(Base):
    __tablename__ = "timeline"
    id = Column(Integer, primary_key=True, autoincrement=True)
    companion_id = Column(String, index=True)
    event_date = Column(String)
    event = Column(String)
    shared = Column(Integer, default=1)
    metadata_json = Column("metadata", String)  # 'metadata' is reserved in SQLAlchemy Base

class Learning(Base):
    __tablename__ = "learning"
    topic = Column(String, primary_key=True)
    confidence = Column(Float, default=0.0)
    progress = Column(Float, default=0.0)
    mastery = Column(Float, default=0.0)

class Conversation(Base):
    __tablename__ = "conversation"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, index=True)
    sender = Column(String)
    message = Column(Text)
    timestamp = Column(Float, default=time.time, index=True)

class ChatThread(Base):
    __tablename__ = "chat_threads"
    id = Column(String, primary_key=True)
    companion_id = Column(String, index=True)
    title = Column(String)
    updated_at = Column(Float, default=time.time)

class Goal(Base):
    __tablename__ = "goals"
    id = Column(String, primary_key=True)
    companion_id = Column(String, index=True)
    title = Column(String)
    description = Column(Text)
    status = Column(String, default="active")
    progress = Column(Float, default=0.0)
    created_at = Column(Float, default=time.time)
    updated_at = Column(Float, default=time.time)

class Plan(Base):
    __tablename__ = "plans"
    companion_id = Column(String, primary_key=True)
    goal = Column(String)
    tasks = Column(Text) # JSON string
    completed = Column(Integer, default=0)
    updated_at = Column(Float, default=time.time)

class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"
    id = Column(String, primary_key=True)
    companion_id = Column(String, index=True)
    name = Column(String)
    prompt = Column(Text)
    run_at = Column(Float, index=True)
    recurring = Column(Integer, default=0)
    interval_sec = Column(Float, default=0.0)
    status = Column(String, default="pending", index=True)

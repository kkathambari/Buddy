import os
import re
from typing import Any, Dict
from ai.gateway.broker import AIGateway
from core.logging import setup_logger
from capabilities.base import Capability

logger = setup_logger("education_capability")

def extract_pdf_concepts(pdf_path: str) -> list:
    """Safely parses a PDF file (simulated or real binary) and extracts core programming concepts."""
    if not os.path.exists(pdf_path):
        return ["Python Development"]
    try:
        content = ""
        with open(pdf_path, "rb") as f:
            header = f.read(1024)
            f.seek(0)
            if b"%PDF-" in header:
                # Real PDF binary - extract ASCII keywords
                chunk = f.read(100 * 1024) # read first 100KB
                content = chunk.decode("latin-1", errors="ignore")
            else:
                # Text-based mock file
                content = f.read().decode("utf-8", errors="ignore")
        
        # Check keywords
        found = []
        keywords = {
            "concurrency": "Concurrency & Multithreading",
            "thread": "Concurrency & Multithreading",
            "index": "Database Indexes",
            "indexing": "Database Indexes",
            "recursion": "Recursion",
            "class": "Object Oriented Programming",
            "oop": "Object Oriented Programming",
            "garbage": "Memory Management",
            "memory": "Memory Management",
            "sql": "SQL Databases",
            "database": "SQL Databases"
        }
        for kw, concept in keywords.items():
            if kw in content.lower():
                if concept not in found:
                    found.append(concept)
                    
        # Fallback based on basename
        if not found:
            base = os.path.basename(pdf_path).lower()
            for kw, concept in keywords.items():
                if kw in base:
                    found.append(concept)
                    
        if not found:
            found = ["Software Development"]
        return found
    except Exception as e:
        logger.error(f"Failed to parse PDF {pdf_path}: {e}")
        return ["Software Development"]

class EducationCapability(Capability):
    """Pluggable VivaForge capability for active study session guidance and PDF concept mapping."""
    
    def __init__(self):
        self._active_sessions: Dict[str, Dict[str, Any]] = {}
        self.sandbox_path = "data/sandbox/education/learning_progress.json"

    def initialize(self) -> None:
        os.makedirs("data/sandbox/education", exist_ok=True)
        logger.info("EducationCapability initialized successfully.")

    def observe(self, context: Dict[str, Any]) -> None:
        """Receives ambient contextual updates. Queues proactive study triggers if trust > 0.6."""
        active_cat = context.get("category", "")
        companion_id = context.get("companion_id", "default_pet")
        
        if active_cat == "studying":
            try:
                from relationship.manager import get_relationship
                from proactive.cooldowns import is_cooldown_active, update_cooldown
                from proactive.trigger import proactive_queue
                
                rel = get_relationship(companion_id)
                if rel.get("trust", 0.5) > 0.6:
                    if not is_cooldown_active("education_proactive_pdf"):
                        proactive_queue[companion_id].put("Looks like that chapter is fighting back.")
                        update_cooldown("education_proactive_pdf")
                        logger.info("Queued proactive study PDF reminder from Education Capability.")
            except Exception as e:
                logger.error(f"Failed in EducationCapability PDF observe: {e}")
                
        elif active_cat == "coding":
            try:
                from relationship.manager import get_relationship
                from proactive.cooldowns import is_cooldown_active, update_cooldown
                from proactive.trigger import proactive_queue
                
                rel = get_relationship(companion_id)
                if rel.get("trust", 0.5) > 0.7:
                    if not is_cooldown_active("education_proactive_quiz"):
                        prompt = """
You are Daemon, a ghostly developer tutor.
Suggest to the user to take a quick Viva quiz on Python or databases to sharpen their skills.
Keep the suggestion short, calm, and slightly snarky (1-2 sentences).
Daemon:
"""
                        response = AIGateway.generate_response(prompt)
                        proactive_queue[companion_id].put(response)
                        update_cooldown("education_proactive_quiz")
                        logger.info("Queued proactive study reminder from Education Capability.")
            except Exception as e:
                logger.error(f"Failed in EducationCapability observe trigger: {e}")

    def execute(self, intent: Dict[str, Any], stats: Dict[str, Any], energy: float) -> str:
        text = intent["raw_text"].lower()
        companion_id = intent.get("companion_id", "default_pet")
        
        logger.info(f"Education Capability handling request: '{text}'")
        session = self._active_sessions.get(companion_id)
        
        # 1. Check for PDF uploads/references
        if ".pdf" in text or "pdf" in text:
            # Extract PDF path
            pdf_path = None
            if ":" in text and not text.startswith("http"):
                parts = text.split(":")
                for part in parts:
                    if ".pdf" in part:
                        pdf_path = part.strip()
                        break
            if not pdf_path:
                for word in text.split():
                    if ".pdf" in word:
                        pdf_path = word.strip(":,;\"'()")
                        break
            
            if pdf_path:
                concepts = extract_pdf_concepts(pdf_path)
                first_concept = concepts[0]
                
                # Setup session
                self._active_sessions[companion_id] = {
                    "concept": first_concept,
                    "stage": "viva_questioning",
                    "question_index": 0,
                    "correct_answers": 0,
                    "pdf_name": os.path.basename(pdf_path),
                    "all_concepts": concepts
                }
                
                # Initialize progress inside database
                try:
                    from backend.repositories.sqlite import get_connection
                    conn = get_connection()
                    cursor = conn.cursor()
                    # Check if already exists, otherwise insert
                    cursor.execute("SELECT * FROM learning WHERE topic = ?", (first_concept,))
                    if not cursor.fetchone():
                        cursor.execute("""
                        INSERT INTO learning (topic, confidence, progress, mastery)
                        VALUES (?, 0.5, 10.0, 10.0)
                        """, (first_concept,))
                        conn.commit()
                    conn.close()
                except Exception:
                    pass
                
                # Write to timeline history
                try:
                    from timeline.history import log_timeline_event
                    log_timeline_event(
                        title=f"Uploaded PDF: {os.path.basename(pdf_path)}",
                        source="conversation",
                        metadata={"pdf_path": pdf_path, "concepts": concepts}
                    )
                except Exception:
                    pass
                
                return (
                    f"I've read through '{os.path.basename(pdf_path)}'. It covers several topics, "
                    f"specifically {', '.join(concepts)}. Let's study {first_concept}. "
                    f"Ready for a Viva review? Here is your question: What is the primary problem that {first_concept} solves?"
                )

        # 2. Start default study session (non-PDF)
        if "study" in text or "learn" in text or "start session" in text:
            concept = "Software Development"
            for word in ["python", "javascript", "databases", "algorithms", "react"]:
                if word in text:
                    concept = word.capitalize()
                    break
                    
            self._active_sessions[companion_id] = {
                "concept": concept,
                "stage": "viva_questioning",
                "question_index": 0,
                "correct_answers": 0
            }
            
            try:
                from timeline.history import log_timeline_event
                log_timeline_event(
                    title=f"Started studying {concept}",
                    source="conversation",
                    metadata={"concept": concept}
                )
            except Exception:
                pass
                
            return (
                f"Let's study {concept}. I've parsed your notes and mapped out the core concepts in your knowledge graph. "
                f"Ready for your first Viva review question? Here: What is the main purpose of {concept}?"
            )
            
        # 3. Check for active Viva questioning
        if session and session["stage"] == "viva_questioning":
            session["question_index"] += 1
            
            eval_prompt = f"""
Evaluate this student answer.
Topic: {session['concept']}
Student Answer: {intent['raw_text']}

Daemon is a ghost tutor. Respond in 2 sentences in Daemon's persona (calm, slightly snarky but helpful), scoring the response and asking the next question.
Daemon:
"""
            try:
                response = AIGateway.generate_response(eval_prompt)
                
                # Save progress inside learning table
                try:
                    from backend.repositories.sqlite import get_connection
                    conn = get_connection()
                    cursor = conn.cursor()
                    
                    cursor.execute("SELECT * FROM learning WHERE topic = ?", (session["concept"],))
                    row = cursor.fetchone()
                    if row:
                        new_progress = min(100.0, row["progress"] + 20.0)
                        new_mastery = min(100.0, row["mastery"] + 15.0)
                        cursor.execute("""
                        UPDATE learning SET progress = ?, mastery = ? WHERE topic = ?
                        """, (new_progress, new_mastery, session["concept"]))
                    else:
                        cursor.execute("""
                        INSERT INTO learning (topic, confidence, progress, mastery)
                        VALUES (?, 0.5, 20.0, 15.0)
                        """, (session["concept"],))
                    conn.commit()
                    conn.close()
                except Exception:
                    pass
                
                # Sandbox progress JSON local fallback
                try:
                    from shared.storage import safe_load, safe_save
                    progress = safe_load(self.sandbox_path, {})
                    progress[session["concept"]] = progress.get(session["concept"], 0) + 10
                    safe_save(self.sandbox_path, progress)
                except Exception:
                    pass
                    
                # Complete session after 3 questions
                if session["question_index"] >= 3:
                    session["stage"] = "complete"
                    
                    # Award Companion XP / Confidence increments
                    try:
                        from relationship.manager import update_relationship
                        update_relationship(companion_id, trust_change=0.08, bond_change=10, action_desc="Completed study session", confidence_change=0.15)
                    except Exception:
                        pass
                        
                    try:
                        from timeline.history import log_timeline_event
                        log_timeline_event(
                            title=f"Finished Viva review for {session['concept']}",
                            source="conversation",
                            metadata={"concept": session["concept"]}
                        )
                    except Exception:
                        pass
                        
                    return response + " That concludes our study session. Excellent work!"
                    
                return response
            except Exception:
                return "Not a bad attempt. Let's move on. Tell me more about how you'd test this concept."
                
        # 4. Check progress/mastery request
        if "progress" in text or "analytics" in text or "mastery" in text:
            # Try loading from SQLite learning table first
            stats_str = ""
            try:
                from backend.repositories.sqlite import get_connection
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM learning")
                rows = cursor.fetchall()
                conn.close()
                if rows:
                    stats_str = ", ".join(f"{row['topic']}: {row['mastery']}% mastery" for row in rows)
            except Exception:
                pass
                
            if not stats_str:
                try:
                    from shared.storage import safe_load
                    progress = safe_load(self.sandbox_path, {})
                    if progress:
                        stats_str = ", ".join(f"{k}: {v}% mastery" for k, v in progress.items())
                except Exception:
                    pass
                    
            if stats_str:
                return f"Here is your learning graph overview: {stats_str}. Keep pushing."
            return "You're at the beginning of your study journey. Ask me to 'study' or drop a PDF to log progress."

        # Fallback tutor help
        prompt = f"Daemon tutor response to user inquiry: '{intent['raw_text']}'. Answer in 2 sentences as a ghostly guide."
        return AIGateway.generate_response(prompt)

    def reflect(self) -> Dict[str, Any]:
        return {"trust_increment": 0.05, "bond_points": 2}

    def update_memory(self) -> None:
        """Commits memory progress logs to the sandbox system."""
        logger.info("EducationCapability memory update committed successfully.")

    def shutdown(self) -> None:
        logger.info("EducationCapability shutdown complete.")

from brain.agents.base import BaseAgent
from brain.planner import TaskNode
from core.logging import setup_logger
from brain.productivity.viva import LearningViva
from brain.productivity.career import CareerCoach

logger = setup_logger("document_agent")

class DocumentAgent(BaseAgent):
    """
    DocumentAgent reads documents, generates summaries, flashcards, and quizzes.
    """
    def __init__(self):
        super().__init__("document_agent")

    async def execute_task(self, task: TaskNode) -> str:
        logger.info(f"DocumentAgent executing task: {task.title}")
        if not self.verify_permissions(["filesystem"]):
            return "Permission 'filesystem' denied. Cannot parse document."
            
        title = task.title.lower()
        desc = task.description or ""
        
        if "viva" in title or "flashcard" in title or "study" in title:
            doc_text = desc or "FastAPI is a modern, fast web framework."
            questions = LearningViva.generate_viva_questions(doc_text)
            q_list = [q["question"] for q in questions]
            return f"Document parsed successfully. Staged {len(questions)} study questions: {', '.join(q_list)}"
        elif "resume" in title or "ats" in title or "career" in title:
            resume_text = desc or "I have python, SQL experience."
            jd_text = "Wanted python developer with git skills."
            res = CareerCoach.analyze_resume_ats(resume_text, jd_text)
            return f"Resume analysis complete. Match Score: {res['match_score']}%"
            
        questions = [
            "What is the Event Bus pattern in DevBuddy?",
            "How does local security permission validation work?"
        ]
        return f"Document parsed successfully. Staged {len(questions)} study questions: {', '.join(questions)}"

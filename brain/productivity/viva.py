import re
from typing import List, Dict, Any
from core.logging import setup_logger

logger = setup_logger("viva")

class LearningViva:
    """
    Learning Viva Compiler.
    Compiles text notes and study guides into interactive flashcard loops.
    """
    @staticmethod
    def generate_viva_questions(text: str) -> List[Dict[str, Any]]:
        """Parses document content and returns list of flashcard questions and answers."""
        questions = []
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        for sentence in sentences:
            sentence_clean = sentence.strip()
            if not sentence_clean:
                continue
                
            # Check 1: Definition match (X is a/an Y, X is defined as Y)
            match_is = re.match(r'^([A-Z][a-zA-Z0-9_\-\s]+)\s+(?:is defined as|is a|is an)\s+(.+)$', sentence_clean)
            if match_is:
                term = match_is.group(1).strip()
                definition = match_is.group(2).strip().rstrip(".")
                questions.append({
                    "question": f"What is {term}?",
                    "answer": f"{term} is {definition}.",
                    "type": "definition"
                })
                continue
                
            # Check 2: Cause/effect match (X occurs when Y, X happens because of Y)
            match_occurs = re.search(r'([A-Z][a-zA-Z0-9_\-\s]+)\s+(?:occurs when|happens because of)\s+(.+)$', sentence_clean)
            if match_occurs:
                event = match_occurs.group(1).strip()
                condition = match_occurs.group(2).strip().rstrip(".")
                questions.append({
                    "question": f"When does {event} occur?",
                    "answer": f"It occurs when {condition}.",
                    "type": "cause_effect"
                })
                
        # Fallback question if none found
        if not questions and len(text.strip()) > 10:
            questions.append({
                "question": "Summarize the primary concept of the provided text.",
                "answer": text.strip()[:200] + "...",
                "type": "summary"
            })
            
        logger.info(f"Viva compiled {len(questions)} study flashcards.")
        return questions

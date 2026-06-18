import os
import time
from typing import Any, Dict
from core.logging import setup_logger
from memory.working_memory import add_dialog_turn
from memory.extractor import evaluate_and_extract
from memory.summarizer import summarize_dialogue_if_needed
from shared.storage import safe_load, safe_save

logger = setup_logger("memory_manager")

def run_memory_aging_sweep() -> None:
    """
    Sweeps through temporary memory caches to age and archive old entries.
    In a complete product, this monitors timestamps. Here we implement the contract rules.
    """
    logger.info("Executing Memory Aging sweep...")
    try:
        # Rules:
        # 1. Archive old coding projects after inactivity (handled on project lists)
        # 2. Deletions of short-term emotion logs
        history_file = "data/emotion_history.json"
        if os.path.exists(history_file):
            history = safe_load(history_file, [])
            if len(history) > 30:
                # Keep only the last 30 emotion logs, aging out the rest
                logger.info(f"Aging out {len(history) - 30} oldest emotion records.")
                safe_save(history_file, history[-30:])
    except Exception as e:
        logger.error(f"Memory aging sweep failed: {e}")

def evaluate_and_commit(user_input: str, response: str, emotion: str = "neutral") -> None:
    """
    Master commit method called at the end of each conversational turn.
    Updates working memory, extracts long-term facts, compresses logs, and sweeps aging.
    """
    logger.info("Memory Manager committing dialogue turn...")
    
    # 1. Update Working Memory
    try:
        add_dialog_turn(user_input, response, emotion)
    except Exception as e:
        logger.error(f"Failed to append dialogue turn to Working Memory: {e}")
        
    # 2. Evaluate Importance and Extract structured metrics (runs asynchronously if score >= 0.7)
    try:
        evaluate_and_extract(user_input)
    except Exception as e:
        logger.error(f"Failed to evaluate and extract facts: {e}")
        
    # 3. Check and summarize dialogue buffers if working memory exceeds 20 turns
    try:
        summarize_dialogue_if_needed()
    except Exception as e:
        logger.error(f"Failed to run dialogue summarization: {e}")
        
    # 4. Periodically run aging check
    try:
        run_memory_aging_sweep()
    except Exception as e:
        logger.error(f"Failed to run memory aging check: {e}")

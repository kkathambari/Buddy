from typing import List, Dict, Any
from ai.gateway.broker import AIGateway
from core.logging import setup_logger
from memory.working_memory import load_working_memory, save_working_memory
from memory.semantic import store_memory

logger = setup_logger("memory_summarizer")

def summarize_dialogue_if_needed() -> None:
    """Checks the working memory size, summarizing older turns if it exceeds 20."""
    memory = load_working_memory()
    if len(memory) <= 20:
        return
        
    logger.info(f"Working memory size ({len(memory)}) exceeds 20 turns. Summarizing oldest 10 turns...")
    
    turns_to_summarize = memory[:10]
    remaining_memory = memory[10:]
    
    # Format dialogue turns for the LLM
    dialogue_str = ""
    for turn in turns_to_summarize:
        dialogue_str += f"User: {turn['user']}\nBuddy: {turn['bot']}\n"
        
    prompt = f"""
Summarize this dialogue segment between the User and Buddy in a single, descriptive paragraph (max 3 sentences).
Focus on specific facts, topics discussed, or achievements unlocked. Do not use generic filler text.

Dialogue:
{dialogue_str}

Summary:
"""
    try:
        summary = AIGateway.generate_response(prompt).strip()
        logger.info(f"Dialogue segment summarized: '{summary[:50]}...'")
        
        # Save to long term semantic vector memory
        store_memory(f"Summary of past dialogue: {summary}")
        
        # Save remaining working memory
        save_working_memory(remaining_memory)
    except Exception as e:
        logger.error(f"Failed to summarize dialogue segment: {e}")

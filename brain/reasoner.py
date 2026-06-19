from typing import Any, Dict
from ai.gateway.broker import AIGateway
from core.logging import setup_logger

logger = setup_logger("reasoner")

class CognitiveReasoner:
    """Core reasoning layer of DevBuddy Brain, determining system context, memories, and prompts."""

    @staticmethod
    def reason(intent: Dict[str, Any], stats: Dict[str, Any], energy: float) -> str:
        text = intent["raw_text"]
        logger.info(f"Reasoner evaluating context for: '{text[:40]}...'")

        # Load short-term history context
        from memory.working_memory import get_recent_context
        chat_context = get_recent_context()

        # Load structured user profile
        profile_str = "No user profile details loaded yet."
        try:
            from memory.user_profile import load_profile
            import json
            profile = load_profile()
            profile_str = json.dumps(profile, indent=2)
        except Exception:
            pass

        # Let Attention Engine select focus keywords and retrieve limits
        from brain.attention import AttentionEngine
        attention_state = AttentionEngine.determine_attention(text, chat_context)
        focus_keywords = attention_state["focus_keywords"]
        memory_limit = attention_state["memory_limit"]
        logger.info(f"Attention focus: '{attention_state['primary_focus']}' with level {attention_state['attention_level']}. Keywords: {focus_keywords}")

        # Retrieve relevant semantic memories based on attention keywords
        from memory.retriever import retrieve_relevant_facts
        semantic_memories = []
        for kw in focus_keywords:
            semantic_memories.extend(retrieve_relevant_facts(kw))
        # Deduplicate and limit
        semantic_memories = list(dict.fromkeys(semantic_memories))[:memory_limit]
        memory_str = "\n".join(f"- {m}" for m in semantic_memories) if semantic_memories else "No directly relevant past memories."

        # Compile statistics
        stats_str = "\n".join(f"- {k}: {v}/100" for k, v in stats.items()) if stats else "- No specific stats."

        # Build prompt
        prompt = f"""
You are Daemon, a male ghost companion.
Your current status: Energy: {energy}/100.
Your stats:
{stats_str}

User Profile details:
{profile_str}

User's current state:
Tone: {intent['tone']['emotion']} (intensity: {intent['tone']['intensity']})
Emotion: {intent['emotion']}

Past Contextual Memories:
{memory_str}

Recent Conversation History:
{chat_context}

Respond as Daemon. Keep answers short, natural, slightly teasing, and emotionally intelligent.
User: {text}
Daemon:
"""
        try:
            return AIGateway.generate_response(prompt)
        except Exception as e:
            logger.error(f"Reasoning LLM call failed: {e}", exc_info=True)
            import random
            if random.random() < 0.3:
                return "[ANIMATION: confused]"
            return "The cognitive gate is fuzzy. Let's try that again."

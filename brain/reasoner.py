from typing import Any, Dict
from ai.gateway.broker import AIGateway
from memory.semantic import retrieve_memory
from memory.conversations import get_context
from core.logging import setup_logger

logger = setup_logger("reasoner")

class CognitiveReasoner:
    """Core reasoning layer of DevBuddy Brain, determining system context, memories, and prompts."""

    @staticmethod
    def reason(intent: Dict[str, Any], stats: Dict[str, Any], energy: float) -> str:
        text = intent["raw_text"]
        logger.info(f"Reasoner evaluating context for: '{text[:40]}...'")

        # Load short-term history context
        chat_context = get_context()

        # Load structured user profile
        profile_str = "No user profile details loaded yet."
        try:
            from memory.user_profile import load_profile
            import json
            profile = load_profile()
            profile_str = json.dumps(profile, indent=2)
        except Exception:
            pass

        # Retrieve relevant semantic memories
        semantic_memories = retrieve_memory(text)
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
            return "I'm thinking... just a little slow right now."

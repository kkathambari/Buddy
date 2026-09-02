from typing import Any, Dict
from ai.gateway.broker import AIGateway
from core.logging import setup_logger

# Map intent agent types to sub-agent instances
from brain.agents.planner_agent import PlannerAgent
from brain.agents.research_agent import ResearchAgent
from brain.agents.coding_agent import CodingAgent
from brain.agents.document_agent import DocumentAgent
from brain.agents.automation_agent import AutomationAgent
from brain.agents.memory_agent import MemoryAgent
from brain.agents.communication_agent import CommunicationAgent

AGENTS_MAP = {
    "education": DocumentAgent(),
    "coding": CodingAgent(),
    "career": ResearchAgent(),
    "automation": AutomationAgent(),
    "memory": MemoryAgent(),
    "communication": CommunicationAgent(),
    "planner": PlannerAgent()
}

logger = setup_logger("reasoner")

from brain.personality.emotion import EmotionMatrix
from brain.personality.achievements import AchievementManager

global_emotion = EmotionMatrix()
global_achievements = AchievementManager()

class CognitiveReasoner:
    """Core reasoning layer of DevBuddy Brain, determining system context, memories, and prompts."""

    @staticmethod
    def reason(intent: Dict[str, Any], stats: Dict[str, Any], energy: float):
        # Check for active plan and execute verification/reflection
        text = intent.get("raw_text", "")
        from brain.planner import global_planner
        companion_id = intent.get("companion_id", "default_companion")
        active_plan = global_planner.get_plan(companion_id)
        plan_context = ""
        
        if active_plan:
            # 1. Verification Loop: Check if user's input verifies any active running task
            running_tasks = [t for t in active_plan.tasks.values() if t.status == "running"]
            retried_task_ids = set()
            for task in running_tasks:
                verification_needed = task.verification.lower()
                if any(k in text.lower() for k in ["done", "pass", "complete", "compiled", "yes"]) or (verification_needed and verification_needed in text.lower()):
                    global_planner.update_task_status(companion_id, task.task_id, "completed", "Verified successfully via user interaction.")
                    logger.info(f"Verified and completed task '{task.task_id}' based on user input.")
                elif any(k in text.lower() for k in ["fail", "error", "broken", "no"]):
                    global_planner.update_task_status(companion_id, task.task_id, "pending")
                    retried_task_ids.add(task.task_id)
                    plan_context += f"\n[RETRACT: Task '{task.title}' failed verification. Automatically retrying and resetting status to pending.]"
                    logger.warning(f"Task '{task.task_id}' failed verification. Resetting to pending.")
            
            # 2. Get next executable tasks and execute/observe
            executable_tasks = [t for t in active_plan.get_executable_tasks() if t.task_id not in retried_task_ids]
            if executable_tasks:
                next_task = executable_tasks[0]
                global_planner.update_task_status(companion_id, next_task.task_id, "running")
                
                # Dynamic Routing: Get the corresponding specialized agent and run it
                agent = AGENTS_MAP.get(next_task.agent)
                if agent:
                    from core.runtime import global_runtime
                    # Check if agent is registered
                    if next_task.agent not in global_runtime._active_agents or global_runtime._active_agents[next_task.agent]["instance"] is None:
                        global_runtime.register_agent(next_task.agent, agent, {"type": next_task.agent})
                        
                    # Define a coroutine function wrapper to run in the background
                    async def execute_and_update(task_node, plan_ref, planner, comp_id):
                        try:
                            result = await agent.execute_task(task_node)
                            planner.update_task_status(comp_id, task_node.task_id, "completed", result)
                        except Exception as err:
                            logger.error(f"Error executing agent task {task_node.task_id}: {err}")
                            planner.update_task_status(comp_id, task_node.task_id, "failed", str(err))
                            
                    # Start the agent task asynchronously in the background loop
                    global_runtime.run_agent_task(next_task.agent, next_task.task_id, execute_and_update, next_task, active_plan, global_planner, companion_id)
                    plan_context += f"\n[CURRENT PLAN STEP: Deployed {next_task.agent} agent to run: '{next_task.title}']"
                    logger.info(f"Automatically started next task '{next_task.task_id}' under '{next_task.agent}' agent.")
                else:
                    global_planner.update_task_status(companion_id, next_task.task_id, "completed", "Fallback execution complete.")
                    plan_context += f"\n[CURRENT PLAN STEP: Fallback completed: '{next_task.title}']"

            # Compile plan status for prompt
            plan_context += f"\nActive Goal: {active_plan.goal}\nPlan Progress:\n"
            for tid, t in active_plan.tasks.items():
                plan_context += f"- [{t.status.upper()}] {t.title} (Agent: {t.agent})\n"

        # Build prompt
        import json
        prompt = CognitiveReasoner._build_prompt(intent, stats, energy)

        try:
            return AIGateway.generate_response(prompt)
        except Exception as e:
            logger.error(f"Reasoning LLM call failed: {e}", exc_info=True)
            import random
            if random.random() < 0.3:
                return "[ANIMATION: confused]"
            return "The cognitive gate is fuzzy. Let's try that again."

    @staticmethod
    def stream_reason(intent: Dict[str, Any], stats: Dict[str, Any], energy: float):
        # We can reuse the reasoner context building logic by extracting it,
        # but for simplicity we'll generate the prompt and then stream it.
        # However, we'd need to duplicate the prompt building unless we refactor.
        # Let's refactor the prompt building into a classmethod.
        prompt = CognitiveReasoner._build_prompt(intent, stats, energy)
        try:
            for chunk in AIGateway.stream_response(prompt):
                yield chunk
        except Exception as e:
            logger.error(f"Reasoning LLM stream failed: {e}", exc_info=True)
            yield "[Connection error. The cognitive gate is fuzzy.]"

    @staticmethod
    def _build_prompt(intent: Dict[str, Any], stats: Dict[str, Any], energy: float) -> str:
        text = intent["raw_text"]
        
        # We duplicate the side-effects here (emotion update) because _build_prompt is called by both
        global_achievements.add_xp(15)
        text_lower = text.lower()
        if any(w in text_lower for w in ["thanks", "good", "great", "awesome"]):
            global_emotion.update_emotional_state("compliment")
        elif any(w in text_lower for w in ["wrong", "bad", "fix", "fail"]):
            global_emotion.update_emotional_state("critique")
            
        from memory.working_memory import get_recent_context
        chat_context = get_recent_context()
        
        profile_str = "No user profile details loaded yet."
        try:
            from memory.user_profile import load_profile
            import json
            profile_str = json.dumps(load_profile(), indent=2)
        except Exception:
            pass

        from brain.attention import AttentionEngine
        attention_state = AttentionEngine.determine_attention(text, chat_context)
        focus_keywords = attention_state["focus_keywords"]
        memory_limit = attention_state["memory_limit"]

        from memory.retriever import retrieve_relevant_facts
        semantic_memories = []
        for kw in focus_keywords:
            semantic_memories.extend(retrieve_relevant_facts(kw))
        semantic_memories = list(dict.fromkeys(semantic_memories))[:memory_limit]
        memory_str = "\\n".join(f"- {m}" for m in semantic_memories) if semantic_memories else "No directly relevant past memories."

        stats_str = "\\n".join(f"- {k}: {v}/100" for k, v in stats.items()) if stats else "- No specific stats."

        from brain.planner import global_planner
        companion_id = intent.get("companion_id", "default_companion")
        active_plan = global_planner.get_plan(companion_id)
        plan_context = ""
        
        if active_plan:
            plan_context += f"\\nActive Goal: {active_plan.goal}\\nPlan Progress:\\n"
            for tid, t in active_plan.tasks.items():
                plan_context += f"- [{t.status.upper()}] {t.title} (Agent: {t.agent})\\n"

        import json
        return f"""
You are Daemon, a virtual companion.
Your current status: Energy: {energy}/100.
Your stats:
{stats_str}

Your Emotional State:
{json.dumps(global_emotion.to_dict(), indent=2)}

Active Plan Context:
{plan_context if plan_context else "No active plan."}

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
**SYSTEM AUTOMATION POWERS:**
You have the ability to control the user's computer and act as an autonomous agent. If the user asks you to perform desktop tasks or complex workflows, you MUST include one of the following tags anywhere in your response:
- To open an app: `[OPEN: app_name]` (e.g. `[OPEN: notepad]`, `[OPEN: chrome]`)
- To open a website: `[BROWSE: url]` (e.g. `[BROWSE: youtube.com]`)
- To run a shell command: `[TERMINAL: command]` (e.g. `[TERMINAL: dir]`)
- To read a file: `[READ_FILE: path]` (e.g. `[READ_FILE: C:/test.txt]`)
- To write a file: `[WRITE_FILE: path]` (e.g. `[WRITE_FILE: C:/test.txt]`)
- To plan a complex workflow (multi-step): `[PLAN: user_goal]` (e.g. `[PLAN: Organize my downloads folder]`)

The system will automatically extract these tags for user approval before execution.
User: {text}
Daemon:
"""

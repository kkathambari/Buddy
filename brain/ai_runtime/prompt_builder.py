"""
Prompt Builder for DevBuddy 2.0 AI Runtime.
Constructs layered, standardized prompts enforcing consistent hierarchy across all agents:
System Prompt -> Developer Instructions -> Conversation -> Memory -> Current Task -> Tool Results -> User Message.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class PromptRequest:
    system_prompt: str = "You are DevBuddy 2.0, an autonomous AI coding companion and desktop assistant."
    developer_instructions: Optional[str] = None
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    memory_context: List[str] = field(default_factory=list)
    current_task: Optional[str] = None
    tool_results: List[Dict[str, Any]] = field(default_factory=list)
    user_message: str = ""
    tools_schema: List[Dict[str, Any]] = field(default_factory=list)
    output_format: Optional[str] = None


@dataclass
class ConstructedPrompt:
    raw_prompt: str
    messages: List[Dict[str, str]]
    tools_schema: List[Dict[str, Any]]
    system_instruction: str


class PromptBuilder:
    """
    Standardized prompt constructor.
    Enforces that all prompts created by any agent or internal component follow the same exact
    structural hierarchy and formatting rules.
    """

    def __init__(self, default_system_prompt: Optional[str] = None):
        self.default_system_prompt = default_system_prompt or (
            "You are DevBuddy 2.0, an autonomous AI coding companion and desktop assistant."
        )

    def build(self, request: PromptRequest) -> ConstructedPrompt:
        """
        Build both a layered string prompt and a standardized list of chat messages.
        """
        # 1. System & Developer instructions
        system_parts = [request.system_prompt or self.default_system_prompt]
        if request.developer_instructions:
            system_parts.append(f"\n[Developer Instructions]\n{request.developer_instructions.strip()}")
        if request.output_format:
            system_parts.append(f"\n[Required Output Format]\n{request.output_format.strip()}")

        system_instruction = "\n".join(system_parts).strip()

        # Build message history for chat providers
        messages: List[Dict[str, str]] = []
        messages.append({"role": "system", "content": system_instruction})

        # 2. Conversation history
        for msg in request.conversation_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if content:
                messages.append({"role": role, "content": str(content).strip()})

        # 3. Build composite user turn payload (Memory -> Current Task -> Tool Results -> User Message)
        user_turn_parts = []

        if request.memory_context:
            mem_text = "\n".join(f"- {m}" for m in request.memory_context if m)
            if mem_text:
                user_turn_parts.append(f"### [Retrieved Memory Context]\n{mem_text}")

        if request.current_task:
            user_turn_parts.append(f"### [Current Task Specification]\n{request.current_task.strip()}")

        if request.tool_results:
            tr_lines = []
            for tr in request.tool_results:
                t_name = tr.get("tool", tr.get("name", "unknown_tool"))
                t_status = tr.get("status", "success")
                t_out = tr.get("output", tr.get("result", ""))
                tr_lines.append(f"Tool: {t_name} (Status: {t_status}) -> {t_out}")
            if tr_lines:
                user_turn_parts.append("### [Tool Execution Results]\n" + "\n".join(tr_lines))

        if request.user_message:
            user_turn_parts.append(f"### [User Message]\n{request.user_message.strip()}")

        composite_user_content = "\n\n".join(user_turn_parts).strip()
        if composite_user_content:
            messages.append({"role": "user", "content": composite_user_content})

        # Build raw string prompt for non-chat/raw completion models
        raw_lines = [f"SYSTEM:\n{system_instruction}\n"]
        for m in messages[1:]:
            role_header = m["role"].upper()
            raw_lines.append(f"{role_header}:\n{m['content']}\n")
        raw_prompt = "\n".join(raw_lines).strip()

        return ConstructedPrompt(
            raw_prompt=raw_prompt,
            messages=messages,
            tools_schema=request.tools_schema,
            system_instruction=system_instruction
        )

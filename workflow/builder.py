"""
Workflow Builder for DevBuddy 2.0 (`workflow/builder.py`).
Converts natural language specifications into structured `WorkflowDefinition` objects using
AI Runtime structured generation or robust rule templates.
"""

import json
import time
from typing import Optional
from .storage import WorkflowDefinition, WorkflowStep
from brain.ai_runtime.runtime import AIRuntimeManager, LLMRequest
from brain.ai_runtime.prompt_builder import PromptRequest


class WorkflowBuilder:
    """
    Constructs executable workflow definitions from natural language prompts.
    """

    @classmethod
    async def build_from_nl(cls, nl_description: str, workflow_id: Optional[str] = None) -> WorkflowDefinition:
        """
        Use AI Runtime to parse user goal into a concrete multi-step workflow.
        """
        w_id = workflow_id or f"wf_{int(time.time())}"

        # If offline/fallback rule template check matches common descriptions
        lower_desc = nl_description.lower()
        if "pr" in lower_desc or "pull request" in lower_desc or "github" in lower_desc:
            steps = [
                WorkflowStep(
                    step_id="step_1_fetch_prs",
                    name="Fetch Open PRs",
                    action_type="tool",
                    parameters={"tool_name": "github", "arguments": {"action": "list_issues"}},
                    next_step_id="step_2_summarize"
                ),
                WorkflowStep(
                    step_id="step_2_summarize",
                    name="Summarize PRs via LLM",
                    action_type="llm",
                    parameters={"prompt": "Summarize the open PRs fetched: {step_1_fetch_prs.output}", "task_hint": "reasoning"},
                    next_step_id=None
                )
            ]
            return WorkflowDefinition(
                workflow_id=w_id,
                name="Auto-Generated GitHub PR Workflow",
                description=nl_description,
                steps=steps
            )

        # General LLM JSON schema extraction
        prompt = (
            f"Convert the following goal into a JSON schema representing a workflow:\n"
            f"Goal: {nl_description}\n"
            f"Required keys: 'name', 'description', 'steps' (list of objects with step_id, name, action_type, parameters, next_step_id)."
        )
        ai = AIRuntimeManager.get_instance()
        req = LLMRequest(
            prompt_request=PromptRequest(user_message=prompt),
            task_hint="reasoning",
            required_json_keys=["name", "description", "steps"]
        )
        resp = await ai.execute(req)

        if resp.validation_result.is_valid and isinstance(resp.validation_result.parsed_json, dict):
            data = resp.validation_result.parsed_json
            steps = [WorkflowStep(**s) for s in data.get("steps", [])]
            return WorkflowDefinition(
                workflow_id=w_id,
                name=data.get("name", "Generated Workflow"),
                description=data.get("description", nl_description),
                steps=steps
            )

        # Fallback single step
        return WorkflowDefinition(
            workflow_id=w_id,
            name="Single-Step LLM Workflow",
            description=nl_description,
            steps=[
                WorkflowStep(
                    step_id="s1",
                    name="Execute Goal",
                    action_type="llm",
                    parameters={"prompt": nl_description, "task_hint": "coding"},
                    next_step_id=None
                )
            ]
        )

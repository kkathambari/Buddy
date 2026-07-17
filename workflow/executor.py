"""
Workflow Executor for DevBuddy 2.0 (`workflow/executor.py`).
Executes individual workflow steps (`llm`, `tool`, `condition`, `assign`), updates instance context data,
and determines the transition target (`next_step_id` or `on_error_step_id`).
"""

import time
import asyncio
from typing import Dict, Any, Tuple, Optional
from .storage import WorkflowStep, WorkflowInstance
from .conditions import ConditionEvaluator
from brain.ai_runtime.runtime import AIRuntimeManager, LLMRequest
from brain.ai_runtime.prompt_builder import PromptRequest
from tools.manager import ToolManager


class WorkflowExecutor:
    """
    Step execution engine coordinating AI Runtime and Tool Manager.
    """

    def __init__(self):
        self.ai_runtime = AIRuntimeManager.get_instance()
        self.tool_manager = ToolManager.get_instance()

    def _render_string(self, text: str, context: Dict[str, Any]) -> str:
        """Simple template substitution replacing `{key}` with context value."""
        if not isinstance(text, str):
            return text
        res = text
        for k, v in context.items():
            if isinstance(v, (str, int, float, bool)):
                res = res.replace(f"{{{k}}}", str(v))
        return res

    def _render_params(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively render parameter variables against context."""
        rendered = {}
        for k, v in params.items():
            if isinstance(v, str):
                rendered[k] = self._render_string(v, context)
            elif isinstance(v, dict):
                rendered[k] = self._render_params(v, context)
            else:
                rendered[k] = v
        return rendered

    async def execute_step(self, step: WorkflowStep, instance: WorkflowInstance) -> Tuple[Optional[str], str]:
        """
        Execute `step` and return `(next_step_id, status)`.
        Updates `instance.context_data` in place with step outputs.
        """
        start_t = time.time()
        rendered_params = self._render_params(step.parameters, instance.context_data)
        history_entry = {
            "step_id": step.step_id,
            "action_type": step.action_type,
            "timestamp": start_t,
            "status": "success"
        }

        try:
            if step.action_type == "llm":
                prompt_t = rendered_params.get("prompt", "")
                task_h = rendered_params.get("task_hint", "chat")
                req = LLMRequest(
                    prompt_request=PromptRequest(user_message=prompt_t),
                    task_hint=task_h
                )
                llm_resp = await self.ai_runtime.execute(req)
                if not llm_resp.validation_result.is_valid:
                    raise RuntimeError(f"LLM validation failed: {llm_resp.validation_result.error_message}")
                instance.context_data[step.step_id] = {
                    "output": llm_resp.text,
                    "model": llm_resp.model_id,
                    "status": "success"
                }

            elif step.action_type == "tool":
                t_name = rendered_params.get("tool_name", "")
                t_args = rendered_params.get("arguments", {})
                t_resp = await self.tool_manager.execute_tool(t_name, t_args)
                if t_resp.status != "success":
                    raise RuntimeError(f"Tool '{t_name}' failed ({t_resp.status}): {t_resp.error_message}")
                instance.context_data[step.step_id] = {
                    "output": t_resp.output,
                    "latency_ms": t_resp.latency_ms,
                    "status": "success"
                }

            elif step.action_type == "condition":
                rule = rendered_params.get("rule", {})
                is_true = ConditionEvaluator.evaluate(rule, instance.context_data)
                instance.context_data[step.step_id] = {"result": is_true, "status": "success"}
                target_id = rendered_params.get("true_step_id") if is_true else rendered_params.get("false_step_id")
                history_entry["latency_ms"] = (time.time() - start_t) * 1000.0
                instance.step_history.append(history_entry)
                return target_id, "success"

            elif step.action_type == "assign":
                key = rendered_params.get("key")
                val = rendered_params.get("value")
                if key:
                    instance.context_data[key] = val
                instance.context_data[step.step_id] = {"assigned": {key: val}, "status": "success"}

            else:
                raise ValueError(f"Unknown action_type: '{step.action_type}'")

            history_entry["latency_ms"] = (time.time() - start_t) * 1000.0
            instance.step_history.append(history_entry)
            return step.next_step_id, "success"

        except Exception as exc:
            history_entry["status"] = "error"
            history_entry["error"] = str(exc)
            history_entry["latency_ms"] = (time.time() - start_t) * 1000.0
            instance.step_history.append(history_entry)
            instance.error_summary = str(exc)
            return step.on_error_step_id, "error"

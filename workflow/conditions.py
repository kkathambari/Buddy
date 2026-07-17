"""
Condition Evaluator for DevBuddy 2.0 (`workflow/conditions.py`).
Evaluates complex composite boolean logic (`AND`, `OR`, `NOT`) against workflow step outputs,
context variables, and system metrics. Supports `==`, `!=`, `>`, `<`, `>=`, `<=`, `contains`, `in`.
"""

from typing import Dict, Any, Union, List


class ConditionEvaluator:
    """
    Evaluates condition expressions or JSON rule trees against context dictionaries.
    Example rule node:
    {"operator": "AND", "rules": [{"field": "status", "op": "==", "value": "success"}, {"field": "count", "op": ">", "value": 5}]}
    """

    @classmethod
    def evaluate(cls, rule: Union[Dict[str, Any], bool], context: Dict[str, Any]) -> bool:
        if isinstance(rule, bool):
            return rule
        if not isinstance(rule, dict):
            return False

        operator = rule.get("operator", "").upper()

        if operator == "AND":
            rules = rule.get("rules", [])
            return all(cls.evaluate(r, context) for r in rules) if rules else True

        elif operator == "OR":
            rules = rule.get("rules", [])
            return any(cls.evaluate(r, context) for r in rules) if rules else False

        elif operator == "NOT":
            sub = rule.get("rule", {})
            return not cls.evaluate(sub, context)

        # Leaf comparison condition (`field`, `op`, `value`)
        field = rule.get("field")
        op = rule.get("op", "==")
        target = rule.get("value")

        if not field:
            return False

        # Resolve field in nested context (e.g., `step_1.output.status`)
        actual = cls._resolve_path(context, field)

        if op == "==":
            return actual == target
        elif op == "!=":
            return actual != target
        elif op == ">":
            return actual > target if actual is not None and target is not None else False
        elif op == "<":
            return actual < target if actual is not None and target is not None else False
        elif op == ">=":
            return actual >= target if actual is not None and target is not None else False
        elif op == "<=":
            return actual <= target if actual is not None and target is not None else False
        elif op in ["contains", "in"]:
            if actual is None or target is None:
                return False
            return target in actual if op == "contains" else actual in target

        return False

    @staticmethod
    def _resolve_path(data: Dict[str, Any], path: str) -> Any:
        parts = path.split(".")
        curr = data
        for part in parts:
            if isinstance(curr, dict) and part in curr:
                curr = curr[part]
            else:
                return None
        return curr

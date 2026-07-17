"""
Response Validator for DevBuddy 2.0 AI Runtime.
Validates LLM outputs against structural schema expectations, extracts code blocks or JSON payloads
from Markdown formatting, and checks for empty or corrupted responses.
"""

import json
import re
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass


@dataclass
class ValidationResult:
    is_valid: bool
    cleaned_output: str
    parsed_json: Optional[Union[Dict[str, Any], List[Any]]] = None
    error_message: Optional[str] = None


class ResponseValidator:
    """
    Validates model completions, strips markdown fences, and checks schema compatibility.
    """

    @staticmethod
    def extract_code_block(text: str, language: Optional[str] = None) -> str:
        """Extract code or JSON from markdown fences (e.g., ```json ... ``` or ```python ... ```)."""
        if not text:
            return ""

        pattern = r"```(?:[a-zA-Z0-9_-]+)?\s*(.*?)\s*```"
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            if language:
                # Try finding exact language match if specified
                lang_pattern = rf"```{re.escape(language)}\s*(.*?)\s*```"
                lang_matches = re.findall(lang_pattern, text, re.DOTALL | re.IGNORECASE)
                if lang_matches:
                    return lang_matches[0].strip()
            return matches[0].strip()
        return text.strip()

    @classmethod
    def validate_json(cls, text: str, required_keys: Optional[List[str]] = None) -> ValidationResult:
        """Extract and parse JSON payload, verifying required keys are present."""
        if not text or not text.strip():
            return ValidationResult(is_valid=False, cleaned_output="", error_message="Empty response received from model.")

        cleaned = cls.extract_code_block(text, language="json")
        try:
            data = json.loads(cleaned)
            if required_keys and isinstance(data, dict):
                missing = [k for k in required_keys if k not in data]
                if missing:
                    return ValidationResult(
                        is_valid=False,
                        cleaned_output=cleaned,
                        parsed_json=data,
                        error_message=f"Response missing required JSON keys: {missing}"
                    )
            return ValidationResult(is_valid=True, cleaned_output=cleaned, parsed_json=data)
        except json.JSONDecodeError as exc:
            return ValidationResult(
                is_valid=False,
                cleaned_output=cleaned,
                error_message=f"Failed to parse JSON: {str(exc)}"
            )

    @classmethod
    def validate_text(cls, text: str, min_length: int = 1) -> ValidationResult:
        """Check raw text output for non-empty completeness."""
        if not text or len(text.strip()) < min_length:
            return ValidationResult(is_valid=False, cleaned_output=text or "", error_message="Output did not meet minimum length check.")
        return ValidationResult(is_valid=True, cleaned_output=text.strip())

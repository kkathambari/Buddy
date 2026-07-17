import re
from typing import List, Dict, Any
from core.logging import setup_logger

logger = setup_logger("coding_assistant")

class CodingAssistant:
    """
    Coding Assistant.
    Analyzes code diffs for quality issues and parses python tracebacks to suggest debug fixes.
    """
    @staticmethod
    def review_pull_request(diff: str) -> List[Dict[str, Any]]:
        """Scans a git diff string and returns code quality annotations."""
        annotations = []
        current_file = "unknown"
        line_num = 0
        
        for line in diff.splitlines():
            # Match file header line
            if line.startswith("+++ b/"):
                current_file = line[6:]
                line_num = 0
                continue
            elif line.startswith("@@"):
                # Rough hunk line parser
                match = re.search(r"\+(\d+)", line)
                if match:
                    line_num = int(match.group(1)) - 1
                continue
                
            # If line is an addition, increment line count and scan contents
            if line.startswith("+"):
                line_num += 1
                content = line[1:].strip()
                
                # Check 1: print calls left in code
                if "print(" in content and not content.startswith("#"):
                    annotations.append({
                        "file": current_file,
                        "line": line_num,
                        "comment": "Avoid committing print statements. Use logger.info() or logger.debug() instead.",
                        "severity": "warning"
                    })
                # Check 2: bare except clauses
                if "except:" in content or "except Exception:" in content:
                    annotations.append({
                        "file": current_file,
                        "line": line_num,
                        "comment": "Catching generic Exception is dangerous. Specify concrete exception classes.",
                        "severity": "error"
                    })
                # Check 3: TODO placeholders
                if "TODO" in content:
                    annotations.append({
                        "file": current_file,
                        "line": line_num,
                        "comment": "Found staged TODO item. Consider implementing it before completing review.",
                        "severity": "info"
                    })
            elif not line.startswith("-"):
                line_num += 1
                
        logger.info(f"PR review complete. Generated {len(annotations)} comments.")
        return annotations

    @staticmethod
    def debug_stack_trace(stack_trace: str) -> Dict[str, Any]:
        """Parses traceback string and returns detailed debug suggestions."""
        # Find file paths and lines
        file_matches = re.findall(r'File "([^"]+)", line (\d+)', stack_trace)
        
        # Get last line (the actual Exception message)
        lines = [l.strip() for l in stack_trace.splitlines() if l.strip()]
        last_line = lines[-1] if lines else "Unknown Error Exception"
        
        if not file_matches:
            return {
                "file": "unknown",
                "line": 0,
                "exception": last_line,
                "suggestion": "Failed to extract code references from stack trace format. Verify file lines."
            }
            
        # Get the deepmost traceback call
        target_file, target_line_str = file_matches[-1]
        target_line = int(target_line_str)
        
        # Build specific suggestions based on exception types
        suggestion = "Review exception conditions and add input validity checks."
        if "KeyError" in last_line:
            suggestion = "The dictionary key is missing. Use .get() or check key presence with `if key in dict:`."
        elif "IndexError" in last_line:
            suggestion = "Sequence index out of range. Check list boundaries or length checks."
        elif "AttributeError" in last_line:
            suggestion = "Attribute or method call is missing on this object instance. Check type instantiation."
        elif "TypeError" in last_line:
            suggestion = "Invalid operand or argument type passed. Add explicit type checks or conversions."
            
        return {
            "file": target_file,
            "line": target_line,
            "exception": last_line,
            "suggestion": suggestion
        }

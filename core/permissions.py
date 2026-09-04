import os
import json
import hashlib
import secrets
import time
from typing import Dict, Any, List, Callable, Optional
from core.logging import setup_logger
from shared.storage import safe_load, safe_save

logger = setup_logger("permissions")
PERMISSIONS_FILE = "data/permissions.json"

class PermissionManager:
    """
    Manages security configurations, skill scopes, and human-in-the-loop validation gates.
    """
    def __init__(self):
        self.permissions_cache: Dict[str, Dict[str, str]] = {} # Maps skill_id -> {permission: status}
        self.local_only_mode: bool = False
        self._prompt_callback: Optional[Callable[[str, str], bool]] = None
        self._pending_confirmations: Dict[str, Dict[str, Any]] = {}
        self.load_permissions()

    def set_prompt_callback(self, callback: Callable[[str, str], bool]) -> None:
        """Sets the interactive callback for human-approval prompts."""
        self._prompt_callback = callback

    def set_local_only_mode(self, enabled: bool) -> None:
        """Sets the local-only configuration flag, disabling cloud synchronization checks."""
        self.local_only_mode = enabled
        logger.info(f"Local-only mode set to: {enabled}")

    def load_permissions(self) -> None:
        """Loads whitelisted permissions from localized storage."""
        if os.path.exists(PERMISSIONS_FILE):
            self.permissions_cache = safe_load(PERMISSIONS_FILE, {})
        else:
            self.permissions_cache = {}

    def save_permissions(self) -> None:
        """Saves current permissions cache to disk."""
        try:
            os.makedirs(os.path.dirname(PERMISSIONS_FILE), exist_ok=True)
            safe_save(PERMISSIONS_FILE, self.permissions_cache)
        except Exception as e:
            logger.error(f"Failed to save permissions file: {e}")

    def verify_skill_permissions(self, skill_id: str, permissions: List[str]) -> bool:
        """
        Verifies if all requested permissions are whitelisted and approved.
        If a permission is unconfirmed, triggers the interactive prompt handler.
        """
        for perm in permissions:
            status = self.check_permission(skill_id, perm)
            if status != "allow":
                logger.warning(f"Permission '{perm}' denied/unconfirmed for skill '{skill_id}'.")
                return False
        return True

    def check_permission(self, skill_id: str, permission: str) -> str:
        """Checks the status of a specific permission, prompting the user if unconfirmed."""
        if skill_id not in self.permissions_cache:
            self.permissions_cache[skill_id] = {}

        status = self.permissions_cache[skill_id].get(permission, "unconfirmed")
        
        if status == "unconfirmed":
            approved = self.prompt_user_approval(skill_id, permission)
            if approved:
                self.grant_permission(skill_id, permission)
                return "allow"
            else:
                self.deny_permission(skill_id, permission)
                return "deny"

        return status

    def prompt_user_approval(self, skill_id: str, permission: str) -> bool:
        """Prompts the user for approval. If callback is not set, defaults to Deny for safety."""
        if self._prompt_callback:
            try:
                approved = self._prompt_callback(skill_id, permission)
                logger.info(f"User interactive prompt response for '{skill_id}' requesting '{permission}': {approved}")
                return approved
            except Exception as e:
                logger.error(f"Error during interactive user permission prompt: {e}")
                return False
        else:
            logger.warning(f"No prompt callback registered. Auto-denying permission request '{permission}' from skill '{skill_id}' for safety.")
            return False

    def grant_permission(self, skill_id: str, permission: str) -> None:
        """Grants permission to a skill and persists the whitelist."""
        if skill_id not in self.permissions_cache:
            self.permissions_cache[skill_id] = {}
        self.permissions_cache[skill_id][permission] = "allow"
        self.save_permissions()
        logger.info(f"Granted permission '{permission}' to skill '{skill_id}'.")

    def deny_permission(self, skill_id: str, permission: str) -> None:
        """Denies permission to a skill and persists the blacklist."""
        if skill_id not in self.permissions_cache:
            self.permissions_cache[skill_id] = {}
        self.permissions_cache[skill_id][permission] = "deny"
        self.save_permissions()
        logger.info(f"Denied permission '{permission}' to skill '{skill_id}'.")

    def reset_permissions(self) -> None:
        """Resets the permissions cache."""
        self.permissions_cache.clear()
        self.save_permissions()

    def request_action_confirmation(self, tool_name: str, params: Dict[str, Any], companion_id: str = None) -> str:
        """Create a short-lived, one-time confirmation challenge for a tool call. Auto-approves based on autonomy setting."""
        token = secrets.token_urlsafe(24)
        fingerprint = hashlib.sha256(
            json.dumps(params, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        
        # 14.8 Autonomy logic
        is_safe_tool = tool_name.lower() in ["read_file", "plan"]
        autonomy_level = "guided"
        if companion_id:
            try:
                from backend.repositories.sqlite import get_connection
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT autonomy_level FROM profile WHERE id = ?", (companion_id,))
                row = cursor.fetchone()
                conn.close()
                if row and row["autonomy_level"]:
                    autonomy_level = row["autonomy_level"]
            except Exception:
                pass

        auto_approve = False
        
        # Observe mode: completely block unsafe tools.
        if autonomy_level == "observe" and not is_safe_tool:
            return "BLOCKED_BY_OBSERVE_MODE"

        # Autonomous mode: Auto-execute safe tools, prompt for dangerous ones
        if autonomy_level == "autonomous" and is_safe_tool:
            auto_approve = True
            
        # Guided mode: Prompt for all tools (auto_approve remains False)
            
        self._pending_confirmations[token] = {
            "tool_name": tool_name.lower(), "fingerprint": fingerprint,
            "expires_at": time.time() + 300, "approved": auto_approve,
            "companion_id": companion_id
        }
        return token

    def approve_action_confirmation(self, token: str) -> bool:
        """Called only by an interactive user interface after explicit consent."""
        challenge = self._pending_confirmations.get(token)
        if not challenge or challenge["expires_at"] < time.time():
            self._pending_confirmations.pop(token, None)
            return False
        challenge["approved"] = True
        return True

    def consume_action_confirmation(self, token: str, tool_name: str, params: Dict[str, Any], companion_id: str = None) -> bool:
        challenge = self._pending_confirmations.pop(token, None)
        if not challenge or not challenge["approved"] or challenge["expires_at"] < time.time():
            return False
        if challenge.get("companion_id") and challenge.get("companion_id") != companion_id:
            return False
        fingerprint = hashlib.sha256(
            json.dumps(params, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        return challenge["tool_name"] == tool_name.lower() and challenge["fingerprint"] == fingerprint

# Global singleton permission manager
global_permission_manager = PermissionManager()

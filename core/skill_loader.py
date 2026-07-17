import importlib.util
import os
import json
from typing import Dict, Any, List
from core.logging import setup_logger
from capabilities.base import Capability
from core.permissions import global_permission_manager

logger = setup_logger("skill_loader")

class SkillLoader:
    """
    Discovers, validates, and dynamically imports plugins/skills at runtime.
    """
    def __init__(self, plugins_dir: str = "skills"):
        self.plugins_dir = plugins_dir
        self.loaded_skills: Dict[str, Dict[str, Any]] = {}

    def discover_and_load_skills(self) -> Dict[str, Dict[str, Any]]:
        """Scans plugins directory and loads all compatible skills."""
        if not os.path.exists(self.plugins_dir):
            os.makedirs(self.plugins_dir, exist_ok=True)
            return {}

        for folder_name in os.listdir(self.plugins_dir):
            skill_path = os.path.join(self.plugins_dir, folder_name)
            if not os.path.isdir(skill_path):
                continue
            
            try:
                self.load_skill(skill_path)
            except Exception as e:
                logger.error(f"Failed to load skill from {folder_name}: {e}", exc_info=True)
        return self.loaded_skills

    def load_skill(self, skill_path: str) -> Dict[str, Any]:
        """Loads a single skill folder, parsing manifest, permissions, and handler class."""
        manifest_path = os.path.join(skill_path, "manifest.json")
        permissions_path = os.path.join(skill_path, "permissions.json")
        handler_path = os.path.join(skill_path, "handler.py")

        if not os.path.exists(manifest_path) or not os.path.exists(handler_path):
            raise FileNotFoundError(f"Missing manifest.json or handler.py in {skill_path}")

        # Read manifest
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        # Validate manifest via SkillManager API
        from core.skill_manager import SkillManager
        if not SkillManager.validate_manifest(manifest):
            raise ValueError(f"Manifest validation failed for skill in '{skill_path}'")

        skill_id = manifest["id"]

        # Read permissions
        permissions = []
        if os.path.exists(permissions_path):
            with open(permissions_path, 'r', encoding='utf-8') as f:
                permissions_data = json.load(f)
                permissions = permissions_data.get("permissions", [])

        # Dynamic import of handler.py
        module_name = f"skill_{skill_id}"
        spec = importlib.util.spec_from_file_location(module_name, handler_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for {handler_path}")
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Discover subclass of Capability
        handler_class = None
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, Capability) and attr is not Capability:
                handler_class = attr
                break
        
        if not handler_class:
            # Fallback to class named Handler or SkillHandler
            for name in ["Handler", "SkillHandler", "AgentHandler"]:
                if hasattr(module, name):
                    handler_class = getattr(module, name)
                    break
        
        if not handler_class:
            raise TypeError(f"Could not find a valid Capability subclass or Handler class in {handler_path}")

        # Check permissions through Global Permission Manager
        allowed = global_permission_manager.verify_skill_permissions(skill_id, permissions)
        if not allowed:
            logger.warning(f"Skill '{skill_id}' requests blocked permissions. Proceeding with caution.")

        # Instantiate handler
        instance = handler_class()
        
        # Initialize
        instance.initialize()

        skill_info = {
            "manifest": manifest,
            "permissions": permissions,
            "instance": instance,
            "path": skill_path,
            "status": "enabled"
        }
        
        self.loaded_skills[skill_id] = skill_info
        logger.info(f"Skill '{skill_id}' loaded and initialized successfully.")
        return skill_info

    def unload_skill(self, skill_id: str) -> None:
        """Gracefully shuts down and unregisters a loaded skill."""
        skill = self.loaded_skills.pop(skill_id, None)
        if skill and hasattr(skill["instance"], "shutdown"):
            try:
                skill["instance"].shutdown()
            except Exception as e:
                logger.error(f"Error shutting down skill '{skill_id}': {e}")
            logger.info(f"Skill '{skill_id}' unloaded.")

    def enable_skill(self, skill_id: str) -> None:
        """Enables a loaded skill."""
        if skill_id in self.loaded_skills:
            self.loaded_skills[skill_id]["status"] = "enabled"
            logger.info(f"Skill '{skill_id}' enabled.")

    def disable_skill(self, skill_id: str) -> None:
        """Disables a loaded skill."""
        if skill_id in self.loaded_skills:
            self.loaded_skills[skill_id]["status"] = "disabled"
            logger.info(f"Skill '{skill_id}' disabled.")

# Global singleton loader
global_skill_loader = SkillLoader()

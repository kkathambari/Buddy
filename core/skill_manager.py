import os
import shutil
import json
from typing import Dict, Any, Optional
from core.logging import setup_logger

logger = setup_logger("skill_manager")

class SkillManager:
    """
    Skill Manager API.
    Handles dynamic checks, deployment validation, and uninstallation cleanups.
    """
    @staticmethod
    def validate_manifest(manifest: Dict[str, Any]) -> bool:
        """Validates that the manifest json has the required schema fields."""
        required_fields = ["id", "name", "version", "description"]
        for field in required_fields:
            if field not in manifest or not manifest[field]:
                logger.warning(f"Manifest validation failed: Missing or empty field '{field}'")
                return False
        return True

    @staticmethod
    def install_skill(skill_dir: str, target_parent_dir: str) -> bool:
        """Installs a skill directory by validating it and copying it to target directory."""
        manifest_path = os.path.join(skill_dir, "manifest.json")
        if not os.path.exists(manifest_path):
            logger.error(f"Cannot install skill: 'manifest.json' not found in '{skill_dir}'")
            return False
            
        try:
            with open(manifest_path, "r") as f:
                manifest = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load manifest.json: {e}")
            return False
            
        if not SkillManager.validate_manifest(manifest):
            return False
            
        skill_id = manifest["id"]
        dest_dir = os.path.join(target_parent_dir, skill_id)
        
        try:
            os.makedirs(target_parent_dir, exist_ok=True)
            if os.path.exists(dest_dir):
                shutil.rmtree(dest_dir)
            shutil.copytree(skill_dir, dest_dir)
            logger.info(f"Successfully installed skill '{skill_id}' to '{dest_dir}'")
            return True
        except Exception as e:
            logger.error(f"Failed copying skill files: {e}")
            return False

    @staticmethod
    def uninstall_skill(skill_id: str, skill_parent_dir: str) -> bool:
        """Safely uninstalls a skill by removing its deployed directory."""
        dest_dir = os.path.join(skill_parent_dir, skill_id)
        if not os.path.exists(dest_dir):
            logger.warning(f"Skill '{skill_id}' not found in '{dest_dir}', skipping uninstallation.")
            return False
            
        try:
            shutil.rmtree(dest_dir)
            logger.info(f"Successfully uninstalled skill '{skill_id}' from '{dest_dir}'")
            return True
        except Exception as e:
            logger.error(f"Failed to delete skill directory: {e}")
            return False

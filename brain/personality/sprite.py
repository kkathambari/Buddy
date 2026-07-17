from core.logging import setup_logger

logger = setup_logger("sprite")

class SpriteSheetAnimator:
    """
    Sprite Sheet Animator.
    Maps emotional mood states to active frame file paths.
    """
    def __init__(self, assets_dir: str = "assets/sprites"):
        self.assets_dir = assets_dir
        # Frame count configurations
        self.state_frames = {
            "idle": 4,
            "thinking": 6,
            "happy": 4,
            "struggling": 8
        }

    def get_animation_frame(self, state: str, frame_index: int) -> str:
        """Returns the frame file path for a companion animation state."""
        state_lower = state.lower()
        if state_lower not in self.state_frames:
            logger.warning(f"Invalid sprite state '{state}', defaulting to 'idle'.")
            state_lower = "idle"
            
        max_frames = self.state_frames[state_lower]
        wrapped_index = frame_index % max_frames
        
        frame_path = f"{self.assets_dir}/companion_{state_lower}_frame_{wrapped_index}.png"
        logger.info(f"Resolved companion frame asset path: '{frame_path}'")
        return frame_path

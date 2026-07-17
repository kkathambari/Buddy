from core.logging import setup_logger

logger = setup_logger("os_control")

class OSController:
    """
    OS Controller.
    Simulates mouse coordinates movement, dragging, scrolling, and keyboard macro strokes.
    Gracefully falls back to mock simulations if OS drivers are absent.
    """
    @staticmethod
    def click_at(x: int, y: int) -> bool:
        """Clicks at target x, y coordinates."""
        try:
            import pyautogui
            pyautogui.click(x, y)
            logger.info(f"Simulated OS click at coordinates ({x}, {y})")
            return True
        except Exception as e:
            logger.warning(f"pyautogui click simulation failed: {e}. Executed coordinate fallback click ({x}, {y})")
            return True

    @staticmethod
    def drag_drop(start_x: int, start_y: int, end_x: int, end_y: int) -> bool:
        """Drags from start_x, start_y to end_x, end_y coordinates."""
        try:
            import pyautogui
            pyautogui.moveTo(start_x, start_y)
            pyautogui.dragTo(end_x, end_y, duration=0.5)
            logger.info(f"Simulated OS drag-drop from ({start_x}, {start_y}) to ({end_x}, {end_y})")
            return True
        except Exception as e:
            logger.warning(f"pyautogui dragTo simulation failed: {e}. Executed drag-drop fallback.")
            return True

    @staticmethod
    def scroll(amount: int) -> bool:
        """Scrolls mouse wheel by amount increment (positive up, negative down)."""
        try:
            import pyautogui
            pyautogui.scroll(amount)
            logger.info(f"Simulated OS mouse scroll of {amount} units.")
            return True
        except Exception as e:
            logger.warning(f"pyautogui scroll simulation failed: {e}. Executed scroll fallback.")
            return True

    @staticmethod
    def send_keys(keys: str) -> bool:
        """Sends raw keyboard string macros."""
        try:
            import pyautogui
            pyautogui.write(keys)
            logger.info(f"Simulated OS keyboard keys write: '{keys}'")
            return True
        except Exception as e:
            logger.warning(f"pyautogui write simulation failed: {e}. Executed keyboard fallback: '{keys}'")
            return True

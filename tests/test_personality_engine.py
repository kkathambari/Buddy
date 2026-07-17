import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add root folder to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from brain.personality.emotion import EmotionMatrix
from brain.personality.achievements import AchievementManager
from brain.personality.sprite import SpriteSheetAnimator
from brain.reasoner import CognitiveReasoner, global_emotion, global_achievements

class TestPersonalityEngine(unittest.TestCase):
    
    def test_emotion_matrix_clamping_and_events(self):
        # Default
        em = EmotionMatrix()
        self.assertEqual(em.happiness, 0.5)
        
        # Clamp upper
        em_high = EmotionMatrix(happiness=2.0)
        self.assertEqual(em_high.happiness, 1.0)
        
        # Clamp lower
        em_low = EmotionMatrix(energy=-1.5)
        self.assertEqual(em_low.energy, 0.0)
        
        # Success event
        em.update_emotional_state("success", delta=0.2)
        self.assertAlmostEqual(em.happiness, 0.7)
        self.assertAlmostEqual(em.focus, 0.7)
        
        # Failure event
        em.update_emotional_state("failure", delta=0.3)
        self.assertAlmostEqual(em.happiness, 0.4)
        
        # Compliment event
        em.update_emotional_state("compliment", delta=0.1)
        self.assertAlmostEqual(em.trust, 0.6)
        
        # Critique event
        em.update_emotional_state("critique", delta=0.2)
        self.assertAlmostEqual(em.trust, 0.4)

    def test_achievement_manager_progression(self):
        am = AchievementManager()
        self.assertEqual(am.level, 1)
        self.assertEqual(am.get_xp_threshold(), 100)
        
        # Add XP (no level-up)
        leveled = am.add_xp(50)
        self.assertFalse(leveled)
        self.assertEqual(am.xp, 50)
        
        # Level up transition
        leveled_up = am.add_xp(60)
        self.assertTrue(leveled_up)
        self.assertEqual(am.level, 2)
        self.assertEqual(am.xp, 10)
        self.assertEqual(am.get_xp_threshold(), 200)
        
        # Multiple level ups
        leveled_multi = am.add_xp(400)
        self.assertTrue(leveled_multi)
        self.assertEqual(am.level, 3)
        
        # Grant achievement
        self.assertTrue(am.grant_achievement("Code Guru"))
        self.assertFalse(am.grant_achievement("Code Guru"))
        self.assertIn("Code Guru", am.achievements)

    def test_sprite_sheet_animator(self):
        sa = SpriteSheetAnimator()
        
        # Standard frame
        path_idle = sa.get_animation_frame("idle", 2)
        self.assertIn("companion_idle_frame_2.png", path_idle)
        
        # Wrap index frame
        path_wrap = sa.get_animation_frame("happy", 5)
        self.assertIn("companion_happy_frame_1.png", path_wrap)
        
        # Invalid state fallback
        path_fallback = sa.get_animation_frame("confused", 0)
        self.assertIn("companion_idle_frame_0.png", path_fallback)

    @patch('ai.gateway.broker.AIGateway.generate_response')
    def test_reasoner_integration_updates(self, mock_generate):
        mock_generate.return_value = "Response"
        
        prev_xp = global_achievements.xp
        prev_happiness = global_emotion.happiness
        
        intent = {
            "raw_text": "Good job, you are amazing companion!",
            "tone": {"emotion": "happy", "intensity": "high"},
            "emotion": "happy"
        }
        CognitiveReasoner.reason(intent, {}, 100)
        
        self.assertEqual(global_achievements.xp, prev_xp + 15)
        self.assertTrue(global_emotion.happiness > prev_happiness)

if __name__ == "__main__":
    unittest.main()

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add root folder to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from ai.gateway.router import ModelRouter
from ai.gateway.broker import AIGateway, global_model_router

class TestModelRouter(unittest.TestCase):
    
    def setUp(self):
        self.router = ModelRouter(cost_limit_cents=10.0)

    def test_routing_by_complexity_and_budget(self):
        # Low complexity -> local
        self.assertEqual(self.router.route_request(complexity="low"), "local_ollama")
        
        # Low budget limit -> local
        self.assertEqual(self.router.route_request(complexity="high", target_budget_cents=0.05), "local_ollama")
        
        # High complexity & budget -> cloud
        self.assertEqual(self.router.route_request(complexity="high", target_budget_cents=1.0), "cloud_gemini")

    def test_spend_accumulation_and_budget_exceeded(self):
        self.router.record_spend(4.5)
        self.assertEqual(self.router.current_spend_cents, 4.5)
        
        # Still under budget
        self.assertEqual(self.router.route_request(complexity="high", target_budget_cents=1.0), "cloud_gemini")
        
        # Exceed budget limit
        self.router.record_spend(6.0)
        self.assertEqual(self.router.route_request(complexity="high", target_budget_cents=1.0), "local_ollama")
        
        # Reset spend
        self.router.reset_spend()
        self.assertEqual(self.router.current_spend_cents, 0.0)
        self.assertEqual(self.router.route_request(complexity="high", target_budget_cents=1.0), "cloud_gemini")

    def test_offline_mode_forces_local_routing(self):
        self.router.offline_mode = True
        self.assertEqual(self.router.route_request(complexity="high", target_budget_cents=2.0), "local_ollama")

    @patch('ai.gateway.broker.AIGateway._call_gemini')
    @patch('ai.gateway.broker.AIGateway._call_ollama')
    def test_gateway_broker_integration(self, mock_ollama, mock_gemini):
        mock_ollama.return_value = "Ollama Response"
        mock_gemini.return_value = "Gemini Response"
        
        global_model_router.reset_spend()
        global_model_router.offline_mode = False
        
        # 1. Low complexity request routes to Ollama
        res = AIGateway.generate_response("simple prompt", complexity="low")
        self.assertEqual(res, "Ollama Response")
        mock_ollama.assert_called_once()
        mock_gemini.assert_not_called()
        
        mock_ollama.reset_mock()
        mock_gemini.reset_mock()
        
        # 2. High complexity routes to Gemini
        res_high = AIGateway.generate_response("complex prompt", complexity="high", budget=1.0)
        self.assertEqual(res_high, "Gemini Response")
        mock_gemini.assert_called_once()
        self.assertTrue(global_model_router.current_spend_cents > 0.0)

    @patch('ai.gateway.broker.AIGateway._call_gemini')
    @patch('ai.gateway.broker.AIGateway._call_ollama')
    def test_gateway_cloud_failure_fallback(self, mock_ollama, mock_gemini):
        mock_ollama.return_value = "Ollama Fallback"
        # Simulate cloud crash exception
        mock_gemini.side_effect = Exception("Cloud offline connection timeout")
        
        global_model_router.reset_spend()
        global_model_router.offline_mode = False
        
        # Request cloud but verify it catches failure and runs local
        res = AIGateway.generate_response("complex prompt", complexity="high", budget=1.0)
        self.assertEqual(res, "Ollama Fallback")
        mock_ollama.assert_called_once()

if __name__ == "__main__":
    unittest.main()

from brain.decision_engine import global_decision_engine
from capabilities.education.handler import handle_education

# Self-registers the capability handler at startup
global_decision_engine.register_capability("education", handle_education)

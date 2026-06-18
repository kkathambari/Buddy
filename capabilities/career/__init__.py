from brain.decision_engine import global_decision_engine
from capabilities.career.handler import handle_career

# Self-registers the capability handler at startup
global_decision_engine.register_capability("career", handle_career)

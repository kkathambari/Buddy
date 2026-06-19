from brain.decision_engine import global_decision_engine
from capabilities.career.handler import CareerCapability

# Self-registers the capability handler instance at startup
global_decision_engine.register_capability("career", CareerCapability())

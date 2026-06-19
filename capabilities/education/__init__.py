from brain.decision_engine import global_decision_engine
from capabilities.education.handler import EducationCapability

# Self-registers the capability handler instance at startup
global_decision_engine.register_capability("education", EducationCapability())

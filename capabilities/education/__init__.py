from brain.router import global_router
from capabilities.education.handler import handle_education

# Self-registers the capability handler at startup
global_router.register_capability("education", handle_education)

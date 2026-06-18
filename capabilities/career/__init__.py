from brain.router import global_router
from capabilities.career.handler import handle_career

# Self-registers the capability handler at startup
global_router.register_capability("career", handle_career)

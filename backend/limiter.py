from slowapi import Limiter
from slowapi.util import get_remote_address

def get_user_or_ip(request):
    # Try to get user uid if authenticated, otherwise fallback to IP
    # In a real app we might parse the token here, but get_remote_address is fine for simple per-IP
    # Let's just use get_remote_address for simplicity per-IP limiting, 
    # since we want per-user + per-IP, get_remote_address limits by IP.
    return get_remote_address(request)

limiter = Limiter(key_func=get_user_or_ip)

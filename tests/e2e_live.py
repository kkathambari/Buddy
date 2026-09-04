import os
import pytest
import requests

# This script is meant to be run against the LIVE production VM
# Usage: pytest tests/e2e_live.py

PROD_URL = os.getenv("BUDDY_PROD_URL", "https://your-domain.com")

@pytest.mark.skipif(not PROD_URL.startswith("http"), reason="No valid production URL configured")
def test_frontend_loads():
    """Verify Caddy is serving the React frontend"""
    res = requests.get(PROD_URL, timeout=10)
    assert res.status_code == 200
    assert "<html" in res.text.lower()
    assert "Buddy" in res.text or "script" in res.text # Basic check for JS app

@pytest.mark.skipif(not PROD_URL.startswith("http"), reason="No valid production URL configured")
def test_backend_health():
    """Verify FastAPI backend is reachable through Caddy"""
    res = requests.get(f"{PROD_URL}/api/health", timeout=10)
    assert res.status_code == 200
    data = res.json()
    assert data.get("status") == "ok"
    assert "postgres_connected" in data

@pytest.mark.skipif(not PROD_URL.startswith("http"), reason="No valid production URL configured")
def test_metrics_protected():
    """Verify Prometheus metrics are NOT exposed to the internet"""
    res = requests.get(f"{PROD_URL}/metrics", timeout=10)
    # Caddy should block or it should not exist in the public router
    assert res.status_code in [404, 403, 401]

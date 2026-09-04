from locust import HttpUser, task, between

class BuddyUser(HttpUser):
    wait_time = between(1, 3)
    token = None
    companion_id = "test_locust_companion"

    def on_start(self):
        # We assume a test user exists or we create one
        # In a real scenario, this would dynamically login
        # For load testing the VM, replace credentials as needed
        response = self.client.post("/api/auth/login", json={
            "email": "loadtest@example.com",
            "password": "password123"
        })
        if response.status_code == 200:
            self.token = response.json().get("access_token")

    @task(3)
    def sync_companion(self):
        if not self.token:
            return
            
        headers = {"Authorization": f"Bearer {self.token}"}
        # Simulate syncing state
        self.client.put(f"/api/sync/{self.companion_id}", json={
            "energy": 90.0,
            "alive": True,
            "stats": {"mood": 80}
        }, headers=headers)
        
    @task(1)
    def get_companion(self):
        if not self.token:
            return
            
        headers = {"Authorization": f"Bearer {self.token}"}
        self.client.get(f"/api/sync/{self.companion_id}", headers=headers)

    @task(1)
    def check_health(self):
        self.client.get("/api/health")

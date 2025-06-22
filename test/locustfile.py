from locust import HttpUser, task, between

class LoadTestUser(HttpUser):
    wait_time = between(1, 1)  # No delay between requests

    @task
    def get_compounds(self):
        with self.client.get(
            "/api/compounds",
            headers={"X-Compound-ID": "1"},
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"❌ Failed with status {response.status_code}")
            else:
                response.success()

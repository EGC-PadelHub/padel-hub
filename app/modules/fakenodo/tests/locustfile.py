from locust import HttpUser, TaskSet, task

from core.environment.host import get_host_for_locust_testing


class FakenodoBehavior(TaskSet):
    def on_start(self):
        """Initialize by listing depositions."""
        self.list_depositions()

    @task(3)
    def list_depositions(self):
        """List all depositions - most frequent operation."""
        response = self.client.get("/fakenodo/depositions")
        if response.status_code != 200:
            print(f"List depositions failed: {response.status_code}")

    @task(2)
    def create_deposition(self):
        """Create a new deposition."""
        response = self.client.post(
            "/fakenodo/depositions",
            json={
                "metadata": {
                    "title": "Test Dataset",
                    "upload_type": "dataset",
                    "description": "Load test deposition",
                    "creators": [{"name": "Locust User"}],
                }
            },
        )
        if response.status_code != 201:
            print(f"Create deposition failed: {response.status_code}")
        else:
            # Store the deposition ID for subsequent operations
            data = response.json()
            deposition_id = data.get("id")
            if deposition_id:
                self.upload_file_to_deposition(deposition_id)
                self.publish_deposition(deposition_id)

    def upload_file_to_deposition(self, rec_id):
        """Upload a file to an existing deposition."""
        response = self.client.post(
            f"/fakenodo/depositions/{rec_id}/files",
            json={"name": "test_file.uvl"},
        )
        if response.status_code != 201:
            print(f"Upload file failed: {response.status_code}")

    def publish_deposition(self, rec_id):
        """Publish a deposition."""
        response = self.client.post(f"/fakenodo/depositions/{rec_id}/actions/publish")
        if response.status_code != 202:
            print(f"Publish deposition failed: {response.status_code}")

    @task(1)
    def get_deposition(self):
        """Get details of a specific deposition (if any exist)."""
        # First, try to get the list to find an existing ID
        response = self.client.get("/fakenodo/depositions")
        if response.status_code == 200:
            depositions = response.json()
            if depositions:
                # Get the first deposition
                rec_id = depositions[0].get("id")
                response = self.client.get(f"/fakenodo/depositions/{rec_id}")
                if response.status_code != 200:
                    print(f"Get deposition failed: {response.status_code}")


class FakenodoUser(HttpUser):
    tasks = [FakenodoBehavior]
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()

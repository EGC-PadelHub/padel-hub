from locust import HttpUser, TaskSet, task

from core.environment.host import get_host_for_locust_testing
from core.locust.common import get_csrf_token


class ProfileBehavior(TaskSet):
    def on_start(self):
        """Initialize by logging in as a test user."""
        self.login()

    def login(self):
        """Login as a test user to access protected profile endpoints."""
        response = self.client.get("/login")
        if response.status_code != 200:
            print(f"Failed to load login page: {response.status_code}")
            return

        csrf_token = get_csrf_token(response)

        response = self.client.post(
            "/login",
            data={"email": "user1@example.com", "password": "1234", "csrf_token": csrf_token},
            catch_response=True,
        )
        if response.status_code != 200:
            print(f"Login failed: {response.status_code}")
            response.failure("Login failed")
        else:
            response.success()

    @task(4)
    def view_metrics_dashboard(self):
        """
        View personal metrics dashboard - most frequent operation.
        Shows uploaded datasets, downloads, views, and synchronizations.
        """
        response = self.client.get("/profile/metrics", catch_response=True)
        if response.status_code != 200:
            print(f"Metrics dashboard access failed: {response.status_code}")
            response.failure("Failed to load metrics dashboard")
        else:
            # Verify key metrics are present in the response
            if (
                b"Uploaded datasets" in response.content
                and b"Downloads of my datasets" in response.content
                and b"Synchronizations" in response.content
            ):
                response.success()
            else:
                response.failure("Metrics dashboard loaded but missing expected content")

    @task(3)
    def view_profile_summary(self):
        """
        View profile summary page with user's datasets.
        """
        response = self.client.get("/profile/summary", catch_response=True)
        if response.status_code != 200:
            print(f"Profile summary access failed: {response.status_code}")
            response.failure("Failed to load profile summary")
        else:
            response.success()

    @task(2)
    def view_profile_summary_paginated(self):
        """
        View profile summary with pagination (page 2).
        """
        response = self.client.get("/profile/summary?page=2", catch_response=True)
        if response.status_code != 200:
            print(f"Profile summary pagination failed: {response.status_code}")
            response.failure("Failed to load paginated profile summary")
        else:
            response.success()

    @task(1)
    def view_edit_profile(self):
        """
        Access the edit profile page.
        """
        response = self.client.get("/profile/edit", catch_response=True)
        if response.status_code != 200:
            print(f"Edit profile page access failed: {response.status_code}")
            response.failure("Failed to load edit profile page")
        else:
            response.success()


class ProfileUser(HttpUser):
    tasks = [ProfileBehavior]
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()

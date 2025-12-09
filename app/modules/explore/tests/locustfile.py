from locust import HttpUser, TaskSet, task
import json

from core.environment.host import get_host_for_locust_testing


class ExploreBehavior(TaskSet):
    def on_start(self):
        """Initialize by loading the explore page."""
        self.load_explore_page()

    @task(5)
    def load_explore_page(self):
        """Load the explore/search page - most frequent operation."""
        response = self.client.get("/explore", catch_response=True)
        if response.status_code != 200:
            print(f"Explore page load failed: {response.status_code}")
            response.failure("Failed to load explore page")
        else:
            response.success()

    @task(4)
    def search_by_title(self):
        """Search datasets by title/name."""
        search_criteria = {"query": "padel", "sorting": "newest", "tournament_type": "any", "tags": []}

        response = self.client.post(
            "/explore",
            data=json.dumps(search_criteria),
            headers={"Content-Type": "application/json"},
            catch_response=True,
        )

        if response.status_code != 200:
            print(f"Search by title failed: {response.status_code}")
            response.failure("Search by title failed")
        else:
            try:
                results = response.json()
                if isinstance(results, list):
                    response.success()
                else:
                    response.failure("Invalid search response format")
            except Exception as e:
                print(f"Error parsing search results: {e}")
                response.failure("Error parsing search results")

    @task(3)
    def search_by_author(self):
        """Search datasets by author name."""
        search_criteria = {
            "query": "",
            "author": "Rodriguez",
            "sorting": "newest",
            "tournament_type": "any",
            "tags": [],
        }

        response = self.client.post(
            "/explore",
            data=json.dumps(search_criteria),
            headers={"Content-Type": "application/json"},
            catch_response=True,
        )

        if response.status_code != 200:
            print(f"Search by author failed: {response.status_code}")
            response.failure("Search by author failed")
        else:
            response.success()

    @task(3)
    def search_with_sorting_oldest(self):
        """Search datasets with sorting by oldest first."""
        search_criteria = {"query": "tournament", "sorting": "oldest", "tournament_type": "any", "tags": []}

        response = self.client.post(
            "/explore",
            data=json.dumps(search_criteria),
            headers={"Content-Type": "application/json"},
            catch_response=True,
        )

        if response.status_code != 200:
            print(f"Search with oldest sorting failed: {response.status_code}")
            response.failure("Search with oldest sorting failed")
        else:
            response.success()

    @task(3)
    def search_with_sorting_newest(self):
        """Search datasets with sorting by newest first."""
        search_criteria = {"query": "dataset", "sorting": "newest", "tournament_type": "any", "tags": []}

        response = self.client.post(
            "/explore",
            data=json.dumps(search_criteria),
            headers={"Content-Type": "application/json"},
            catch_response=True,
        )

        if response.status_code != 200:
            print(f"Search with newest sorting failed: {response.status_code}")
            response.failure("Search with newest sorting failed")
        else:
            response.success()

    @task(2)
    def search_by_tournament_type(self):
        """Search datasets filtered by tournament type."""
        search_criteria = {"query": "", "sorting": "newest", "tournament_type": "internacional", "tags": []}

        response = self.client.post(
            "/explore",
            data=json.dumps(search_criteria),
            headers={"Content-Type": "application/json"},
            catch_response=True,
        )

        if response.status_code != 200:
            print(f"Search by tournament type failed: {response.status_code}")
            response.failure("Search by tournament type failed")
        else:
            response.success()

    @task(2)
    def search_by_tags(self):
        """Search datasets filtered by tags."""
        search_criteria = {"query": "", "sorting": "newest", "tournament_type": "any", "tags": ["padel", "sports"]}

        response = self.client.post(
            "/explore",
            data=json.dumps(search_criteria),
            headers={"Content-Type": "application/json"},
            catch_response=True,
        )

        if response.status_code != 200:
            print(f"Search by tags failed: {response.status_code}")
            response.failure("Search by tags failed")
        else:
            try:
                results = response.json()
                if isinstance(results, list):
                    response.success()
                else:
                    response.failure("Invalid search response format")
            except Exception as e:
                print(f"Error parsing tag search results: {e}")
                response.failure("Error parsing tag search results")

    @task(2)
    def search_by_description(self):
        """Search datasets by description content."""
        search_criteria = {
            "query": "",
            "description": "professional players",
            "sorting": "newest",
            "tournament_type": "any",
            "tags": [],
        }

        response = self.client.post(
            "/explore",
            data=json.dumps(search_criteria),
            headers={"Content-Type": "application/json"},
            catch_response=True,
        )

        if response.status_code != 200:
            print(f"Search by description failed: {response.status_code}")
            response.failure("Search by description failed")
        else:
            response.success()

    @task(1)
    def complex_search(self):
        """
        Complex search combining multiple filters:
        - Title query
        - Tags filter
        - Tournament type filter
        - Sorting
        """
        search_criteria = {
            "query": "padel",
            "sorting": "newest",
            "tournament_type": "internacional",
            "tags": ["professional"],
        }

        response = self.client.post(
            "/explore",
            data=json.dumps(search_criteria),
            headers={"Content-Type": "application/json"},
            catch_response=True,
        )

        if response.status_code != 200:
            print(f"Complex search failed: {response.status_code}")
            response.failure("Complex search failed")
        else:
            try:
                results = response.json()
                if isinstance(results, list):
                    response.success()
                else:
                    response.failure("Invalid complex search response format")
            except Exception as e:
                print(f"Error parsing complex search results: {e}")
                response.failure("Error parsing complex search results")

    @task(1)
    def explore_with_query_params(self):
        """Load explore page with query parameters."""
        response = self.client.get("/explore?query=padel+tournament", catch_response=True)
        if response.status_code != 200:
            print(f"Explore with query params failed: {response.status_code}")
            response.failure("Failed to load explore with query params")
        else:
            response.success()


class ExploreUser(HttpUser):
    tasks = [ExploreBehavior]
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()

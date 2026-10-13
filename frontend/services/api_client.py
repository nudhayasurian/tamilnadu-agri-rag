
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
).rstrip("/")


class ApiClient:
    def __init__(self):
        self.client = httpx.Client(
            base_url=BASE_URL,
            timeout=30,
        )

    def health(self):
        response = self.client.get("/api/v1/health")
        response.raise_for_status()
        return response.json()

    def stats(self):
        response = self.client.get("/api/v1/stats")
        response.raise_for_status()
        return response.json()

    def search(self, query, top_k, language, max_distance):
        response = self.client.post(
            "/api/v1/search",
            json={
                "query": query,
                "top_k": top_k,
                "language": language,
                "max_distance": max_distance,
            },
        )
        response.raise_for_status()
        return response.json()

    def close(self):
        self.client.close()

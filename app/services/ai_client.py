import httpx
from typing import Dict, List

class AIClient:
    # Use a single shared client for connection pooling
    # This prevents creating a new TCP connection and TLS handshake for every request
    _client = None

    def __init__(self, ai_url: str = "http://localhost:8002"):
        self.ai_url = ai_url

    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        if cls._client is None:
            cls._client = httpx.AsyncClient()
        return cls._client

    @classmethod
    async def close(cls):
        if cls._client is not None:
            await cls._client.aclose()
            cls._client = None

    async def decide(self, state_snapshot: Dict) -> List[Dict]:
        client = self.get_client()
        response = await client.post(
            f"{self.ai_url}/decide",
            json=state_snapshot,
        )
        if response.status_code == 200:
            return response.json().get("actions", [])
        return []

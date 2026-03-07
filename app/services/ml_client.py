import httpx
from typing import Dict, Optional

class MLClient:
    # Use a single shared client for connection pooling
    # This prevents creating a new TCP connection and TLS handshake for every request
    _client = None

    def __init__(self, gateway_url: str = "http://localhost:8001"):
        self.gateway_url = gateway_url

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

    async def infer(self, image_data: bytes, tasks: list) -> Optional[Dict]:
        client = self.get_client()
        response = await client.post(
            f"{self.gateway_url}/api/v1/ml/infer",
            files={"image": image_data},
            data={"tasks": ",".join(tasks)},
        )
        if response.status_code == 200:
            return response.json()
        return None

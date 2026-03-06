import httpx
from typing import Dict, Optional

class MLClient:
    def __init__(self, gateway_url: str = "http://localhost:8001"):
        self.gateway_url = gateway_url

    async def infer(self, image_data: bytes, tasks: list) -> Optional[Dict]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.gateway_url}/api/v1/ml/infer",
                files={"image": image_data},
                data={"tasks": ",".join(tasks)},
            )
            if response.status_code == 200:
                return response.json()
            return None

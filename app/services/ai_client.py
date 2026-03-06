import httpx
from typing import Dict, List

class AIClient:
    def __init__(self, ai_url: str = "http://localhost:8002"):
        self.ai_url = ai_url

    async def decide(self, state_snapshot: Dict) -> List[Dict]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.ai_url}/decide",
                json=state_snapshot,
            )
            if response.status_code == 200:
                return response.json().get("actions", [])
            return []

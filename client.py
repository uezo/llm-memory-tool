from datetime import datetime, timezone
import httpx


class MemoryClient:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        timeout: float = 5.0
    ):
        self.base_url = base_url
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout=timeout)
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.http_client.aclose()

    async def add_message(
        self,
        conversation_id: str,
        user_id: str,
        query: str,
        answer: str,
        created_at: datetime = None
    ):
        await self.http_client.post(
            url=self.base_url + "/messages",
            json={
                "data": [{
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "query": query,
                    "answer": answer,
                    "created_at": (created_at or datetime.now(timezone.utc)).isoformat()
                }]
            }
        )

    async def get_memory(
        self,
        query: str,
        user_id: str,
        limit: int = 5
    ):
        resp = await self.http_client.get(
            url=self.base_url + "/summaries",
            params={
                "query": query,
                "user_id": user_id,
                "limit": limit
            }
        )

        return resp.json()

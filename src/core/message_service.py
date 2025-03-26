"""Message service for processing and querying Discord messages."""

from typing import Dict, List, Optional

from src.models.discord_models import MessageModel
from src.services.discord_service import DiscordService
from src.services.rag_service import RAGService


class MessageService:
    """Service for handling Discord message retrieval and querying."""

    def __init__(self) -> None:
        """Initialize the message service."""
        self.discord_service = DiscordService()
        self.rag_service: Optional[RAGService] = None
        self._messages: List[MessageModel] = []

    async def close(self) -> None:
        """Close the underlying services."""
        await self.discord_service.close()

    async def fetch_messages(self, limit_per_channel: int = 50) -> List[MessageModel]:
        """Fetch messages from all guilds and channels."""
        self._messages = await self.discord_service.fetch_messages_from_all_guilds(
            limit_per_channel=limit_per_channel
        )
        return self._messages

    async def process_messages(self) -> None:
        """Process fetched messages and prepare them for querying."""
        if not self._messages:
            await self.fetch_messages()

        self.rag_service = RAGService(self._messages)
        processed_data = self.rag_service.process_messages()
        self.rag_service.create_index(processed_data)

    async def query_messages(
        self, query: str, min_score: float = 0.0, top_k: int = 10
    ) -> List[Dict]:
        """Query messages using RAG."""
        if not self.rag_service:
            await self.process_messages()
            if not self.rag_service:
                return []

        results = self.rag_service.query_messages(query, top_k=top_k)

        # Filter results by minimum score
        filtered_results = [
            result for result in results if result["score"] >= min_score
        ]
        return filtered_results

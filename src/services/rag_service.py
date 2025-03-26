"""RAG service for processing and querying Discord messages."""

from datetime import datetime
from typing import Any, Dict, List

from llama_index.core import VectorStoreIndex
from llama_index.core.schema import TextNode
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.faiss import FaissVectorStore

from src.models.discord_models import MessageModel


class RAGService:
    """Service for processing and querying Discord messages using RAG."""

    def __init__(self, messages: List[MessageModel]):
        self.messages = messages
        self._index = None

    def process_messages(self) -> Dict[str, Dict[str, Any]]:
        """Process messages and convert them to a format suitable for indexing."""
        message_dict = {}
        for msg in self.messages:
            message_dict[msg.id] = msg.model_dump()
        return message_dict

    def create_index(self, processed_data: Dict[str, Any]) -> VectorStoreIndex:
        """Create a vector index from processed Discord messages."""
        # Create nodes from messages
        nodes = []

        for msg_id, msg_data in processed_data.items():
            # Create text with metadata
            text = f"{msg_data['author']['username']} said: {msg_data['content']}"

            # Add reply context if available
            if msg_data.get("message_reference"):
                parent_id = msg_data["message_reference"]["message_id"]
                if parent_id in processed_data:
                    parent = processed_data[parent_id]
                    text = f"{text}\n[In reply to {parent['author']['username']} who said: {parent['content']}]"

            # Create node with metadata
            node = TextNode(
                text=text,
                metadata={
                    "message_id": msg_id,
                    "author": msg_data["author"]["username"],
                    "timestamp": (
                        msg_data["timestamp"]
                        if isinstance(msg_data["timestamp"], str)
                        else msg_data["timestamp"].isoformat()
                    ),
                    "channel_id": msg_data["channel_id"],
                },
            )
            nodes.append(node)

        # Create embedding model
        embed_model = HuggingFaceEmbedding(model_name="all-MiniLM-L6-v2")

        # Create faiss index
        import faiss

        dimension = 384  # Using default dim for all-MiniLM-L6-v2
        faiss_index = faiss.IndexFlatL2(dimension)

        # Create vector store with the faiss index
        vector_store = FaissVectorStore(faiss_index=faiss_index)

        # Create index
        index = VectorStoreIndex(
            nodes=nodes, vector_store=vector_store, embed_model=embed_model
        )

        self._index = index
        return index

    def query_messages(self, query: str, top_k: int = 10) -> List[Dict]:
        """Query the index for relevant messages."""
        if not self._index:
            raise ValueError("Index has not been created. Call create_index first.")

        retriever = self._index.as_retriever(similarity_top_k=top_k)
        nodes = retriever.retrieve(query)
        results = []
        for node in nodes:
            results.append(
                {"text": node.text, "score": node.score, "metadata": node.metadata}
            )

        return results

from datetime import datetime
from typing import Any, Dict, List

from llama_index.core import VectorStoreIndex
from llama_index.core.schema import TextNode
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.faiss import FaissVectorStore
from pydantic import BaseModel

from .client.discord_api import MessageModel


class AuthorModel(BaseModel):
    username: str
    id: str


class MessageReferenceModel(BaseModel):
    message_id: str
    channel_id: str


# class MessageModel(BaseModel):
#     id: str
#     content: str
#     channel_id: str
#     author: AuthorModel
#     timestamp: datetime
#     message_reference: MessageReferenceModel = None

#     def to_dict(self):
#         result = {
#             "id": self.id,
#             "content": self.content,
#             "channel_id": self.channel_id,
#             "author": self.author.username,
#             "timestamp": self.timestamp.isoformat(),
#         }
#         if self.message_reference:
#             result["refers_to"] = self.message_reference.message_id
#         return result


# Sample messages (simplified version of your examples)
def get_sample_messages() -> List[MessageModel]:
    """Returns sample Discord messages for testing"""
    return [
        MessageModel(
            id="1354327688420130920",
            content="reply message",
            channel_id="1354301439358406690",
            author=AuthorModel(username="alex_lau.", id="471724827091271682"),
            timestamp=datetime(2025, 3, 26, 5, 34, 43),
            message_reference=MessageReferenceModel(
                message_id="1354325603943317596", channel_id="1354301439358406690"
            ),
        ),
        MessageModel(
            id="1354325603943317596",
            content="Testing message",
            channel_id="1354301439358406690",
            author=AuthorModel(username="outrageous_duck", id="1340866997264580719"),
            timestamp=datetime(2025, 3, 26, 5, 26, 26),
        ),
        MessageModel(
            id="1354324552666321046",
            content="the fox say moooooo",
            channel_id="1354301439358406690",
            author=AuthorModel(username="alex_lau.", id="471724827091271682"),
            timestamp=datetime(2025, 3, 26, 5, 22, 15),
            message_reference=MessageReferenceModel(
                message_id="1354324524862013550", channel_id="1354301439358406690"
            ),
        ),
        MessageModel(
            id="1354324552666321088",
            content="the cat says capybara",
            channel_id="1354301439358406690",
            author=AuthorModel(username="alex_lau.", id="471724827091271682"),
            timestamp=datetime(2025, 3, 26, 5, 30, 15),
        ),
    ]

class MessageProcessor:
    def __init__(self, messages: List[MessageModel]):
        self.messages = messages

    def process_messages(self) -> Dict[str, Dict[str, Any]]:
        """Process messages and convert them to a format suitable for indexing"""
        message_dict = {}
        for msg in self.messages:
            message_dict[msg.id] = msg.model_dump()
        return message_dict


    def create_llama_index(self, processed_data: Dict[str, Any]) -> VectorStoreIndex:
        """Create LlamaIndex from processed Discord messages"""
        # Create nodes from messages
        nodes = []

        for msg_id, msg_data in processed_data.items():
            # Create text with metadata
            text = f"{msg_data['author']['username']} said: {msg_data['content']}"

            # Add reply context if available
            if msg_data.get('message_reference'):
                parent_id = msg_data['message_reference']['message_id']
                if parent_id in processed_data:
                    parent = processed_data[parent_id]
                    text = f"{text}\n[In reply to {parent['author']['username']} who said: {parent['content']}]"

            # Create node with metadata
            node = TextNode(
                text=text,
                metadata={
                    "message_id": msg_id,
                    "author": msg_data['author']['username'],
                    "timestamp": msg_data['timestamp'].isoformat(),
                    "channel_id": msg_data['channel_id'],
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

        return index


    def query_discord_messages(
        self, index: VectorStoreIndex, query: str, top_k: int
    ) -> List[Dict]:
        """Query the index for relevant messages"""
        retriever = index.as_retriever(similarity_top_k=top_k)
        nodes = retriever.retrieve(query)
        results = []
        for node in nodes:
            results.append(
                {"text": node.text, "score": node.score, "metadata": node.metadata}
            )

        return results


def main():
    messages = get_sample_messages()
    message_processor = MessageProcessor(messages)
    processed_data = message_processor.process_messages()
    index = message_processor.create_llama_index(processed_data)
    query = "What does the fox say?"
    results = message_processor.query_discord_messages(index, query, top_k=10)

    # Print results
    print(f"Query: {query}")
    print("Results:")
    for i, result in enumerate(results):
        print(f"\n--- Result {i+1} ---")
        print(f"Text: {result['text']}")
        print(f"Score: {result['score']}")
        print(f"Author: {result['metadata']['author']}")
        print(f"Timestamp: {result['metadata']['timestamp']}")
    return results


if __name__ == "__main__":
    results = main()

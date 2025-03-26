from datetime import datetime
from typing import Any, Dict, List

from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.schema import TextNode
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.faiss import FaissVectorStore
from pydantic import BaseModel


# Models for Discord messages (simplified from your example)
class AuthorModel(BaseModel):
    username: str
    id: str


class MessageReferenceModel(BaseModel):
    message_id: str
    channel_id: str


class MessageModel(BaseModel):
    id: str
    content: str
    channel_id: str
    author: AuthorModel
    timestamp: datetime
    message_reference: MessageReferenceModel = None

    def to_dict(self):
        result = {
            "id": self.id,
            "content": self.content,
            "channel_id": self.channel_id,
            "author": self.author.username,
            "timestamp": self.timestamp.isoformat(),
        }
        if self.message_reference:
            result["refers_to"] = self.message_reference.message_id
        return result


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


def process_messages(messages: List[MessageModel]) -> Dict[str, Any]:
    """Process messages and maintain their relationships"""
    # Create a dictionary to store messages by ID
    message_dict = {}
    threads = {}

    # First pass: store all messages
    for msg in messages:
        message_dict[msg.id] = msg.to_dict()

        # Track thread relationships
        if msg.message_reference:
            parent_id = msg.message_reference.message_id
            if parent_id not in threads:
                threads[parent_id] = []
            threads[parent_id].append(msg.id)

    # Second pass: enhance messages with thread information
    for msg_id, thread_replies in threads.items():
        if msg_id in message_dict:
            message_dict[msg_id]["replies"] = thread_replies

    return {"messages": message_dict, "threads": threads}


def create_llama_index(processed_data: Dict[str, Any]) -> VectorStoreIndex:
    """Create LlamaIndex from processed Discord messages"""
    # Create nodes from messages
    nodes = []

    for msg_id, msg_data in processed_data["messages"].items():
        # Create text with metadata
        text = f"{msg_data['author']} said: {msg_data['content']}"

        # Add reply context if available
        if "refers_to" in msg_data:
            parent_id = msg_data["refers_to"]
            if parent_id in processed_data["messages"]:
                parent = processed_data["messages"][parent_id]
                text = f"{text}\n[In reply to {parent['author']} who said: {parent['content']}]"

        # Create node with metadata
        node = TextNode(
            text=text,
            metadata={
                "message_id": msg_id,
                "author": msg_data["author"],
                "timestamp": msg_data["timestamp"],
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

    return index


def query_discord_messages(
    index: VectorStoreIndex, query: str, top_k: int
) -> List[Dict]:
    """Query the index for relevant messages"""
    # Create query engine with explicit retriever to bypass LLM usage
    retriever = index.as_retriever(similarity_top_k=top_k)

    # Retrieve nodes directly without using LLM
    nodes = retriever.retrieve(query)

    # Format results
    results = []
    for node in nodes:
        results.append(
            {"text": node.text, "score": node.score, "metadata": node.metadata}
        )

    return results


def main():
    # Get sample messages
    messages = get_sample_messages()

    # Process messages
    processed_data = process_messages(messages)

    # Create index
    index = create_llama_index(processed_data)

    # Example query
    query = "What does the fox say?"
    results = query_discord_messages(index, query, top_k=10)

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

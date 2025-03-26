## Project Overview

The discord Q&A command line application allows users to ask questions based on discord channels. User can specify which channels to ask questions and the application will download the chat history of that channel to build a local RAG. Next, user can ask different questions and LLM should be able to answer the questions using the embeddings/context of the downloaded channel history.

## Core Functionalities

This application should be a lightweight CLI tool written in Python with the following key features:

1. User Credentials Configuration: it help user configure the required credentials (e.g. API key) for accessing its discord account information (e.g. messages from different server and channels)
2. Server and Channel Navigation: the CLI should provide interfaces for user to list available discord servers, and then list available channels for the selected server
3. Pulling Messages to Local Storage: user can select server name and channel name, and then the CLI should be able to pull all the messages to local storage
   - you should preserve the structure of the messages, for example the lineage if its a reply message or if its a thread
   - you should preserve the metadata, e.g. username, emojis reaction to the message, posted time
   - for now, please only focus on the text (can include emoji) in the messages and you can skip multimedia if user attach them to the message (e.g. video, sticker, picture)
4. RAG based on user query: users can ask a question to a server’s channel, and the CLI should be able to retrieve messages that are semantically relevant. The CLI should search through the channel’s messages that are locally storage in previous step
   - the retrieved messages should preserve the lineage structure as well (e.g. if the retrieved messages contain reply or is a thread, you should also retrieve them with structure preserved)
   - to make things simple at the beginning, please suggest a few options of RAG techniques and toolstack that is simple enough to configure and run
   - if RAG requires preprocessing step (e.g. precomputation of embedding), you could dispatch the preprocessing step to feature (3) above
5. Q&A Chat feature: this is a follow up of (4), after retrieving the relevant messages, you submit the user question together with the additional
   - you should create a prompt template that works well to Q&A with LLM models, and the application will inject both user question and retrieved messages as additional context to the prompt, and finally submit to LLM model
   - for now, let’s consider Gemini API, so the application should integrate with Gemini API and submit the prompt, the CLI should return the API response at the end

## Desired File Structure

```
discord-qna-bot/
├── pyproject.toml           # Poetry project configuration
├── .env                     # Environment variables
├── README.md                # Project documentation
└── src/                     # Source code directory
    ├── __init__.py
    ├── main.py              # Entry point
    ├── config/              # Configuration-related modules
    │   ├── __init__.py
    │   └── settings.py      # Renamed from config.py
    ├── api/                 # API-related modules
    │   ├── __init__.py
    │   └── discord_client.py  # Renamed from discord_api.py
    ├── auth/                # Authentication-related modules
    │   ├── __init__.py
    │   ├── oauth_server.py  # OAuth server implementation
    │   └── token_manager.py # Renamed from token_storage.py
    ├── core/                # Core application logic
    │   ├── __init__.py
    │   ├── dependencies.py  # Application dependencies
    │   └── message_service.py  # New file for message processing logic
    ├── models/              # Data models
    │   ├── __init__.py
    │   ├── discord_models.py  # Discord entity models
    │   └── token_models.py    # Token-related models
    └── services/            # Business logic services
        ├── __init__.py
        ├── rag_service.py   # Renamed from rag_llama_index_faiss.py
        └── discord_service.py  # New file for Discord-specific logic
```

## Additional Requirements

1. security: please store user credentials (e.g. API key) safely at .env and read them using dotenv package
2. please use poetry to manage dependencies of our python project

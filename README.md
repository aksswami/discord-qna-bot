# Discord QnA Bot

A Discord bot that uses Retrieval-Augmented Generation (RAG) to answer questions based on Discord message history.

## Features

- OAuth2 authentication with Discord
- Fetch messages from Discord channels
- Process messages using FAISS vector index
- Answer questions based on message history using semantic search

## Architecture

The project follows a clean architecture approach with the following components:

- **API Layer**: Low-level interaction with Discord API
- **Auth Layer**: Authentication and token management
- **Core Layer**: Application business logic
- **Models**: Data models for application entities
- **Services**: Business logic services
- **Config**: Application configuration management

## Installation

### Prerequisites

- Python 3.9+
- Poetry (dependency management)

### Setup

1. Clone the repository:

   ```
   git clone https://github.com/yourusername/discord-qna-bot.git
   cd discord-qna-bot
   ```

2. Install dependencies:

   ```
   poetry install
   ```

3. Create a `.env` file in the root directory with the following content:
   ```
   APP_DISCORD__CLIENT_ID=your_discord_client_id
   APP_DISCORD__CLIENT_SECRET=your_discord_client_secret
   APP_DISCORD__REDIRECT_URI=http://localhost:8000/oauth2/callback
   APP_DISCORD__BOT_TOKEN=your_discord_bot_token
   APP_SERVER__HOST=0.0.0.0
   APP_SERVER__PORT=8000
   ```

## Usage

### Running the Bot

```
poetry run discord-qna-bot
```

This will start the bot in the message query mode, which will:

1. Fetch messages from all accessible Discord channels
2. Process them using a FAISS vector index
3. Allow you to query messages using natural language

### Development

- Format code: `poetry run black src`
- Sort imports: `poetry run isort src`
- Type checking: `poetry run mypy src`
- Linting: `poetry run flake8 src`

## License

This project is licensed under the MIT License - see the LICENSE file for details.

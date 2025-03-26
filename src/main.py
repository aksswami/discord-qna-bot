# -*- coding: utf-8 -*-
"""Main entry point for the discord-qna-bot CLI."""

import asyncio
import sys
import webbrowser
from asyncio import sleep
from typing import Optional

import uvicorn
from colorama import Fore, Style

from src.api.discord_client import DiscordClient
from src.auth.oauth_server import app
from src.auth.token_manager import TokenManager
from src.config.settings import settings
from src.core.message_service import MessageService
from src.models.discord_models import TokenType


async def run_server(host: str, port: int) -> None:
    """Run the FastAPI server using uvicorn."""
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def async_main_user_flow() -> None:
    """Async main function for the user authentication flow."""
    # Initialize token manager
    token_manager = TokenManager()

    # Check for existing token
    latest_token = token_manager.get_latest_token()
    if latest_token and not latest_token.is_expired():
        print("Using existing token...")
        discord = DiscordClient(
            token=latest_token.access_token, token_type=TokenType.USER
        )
    else:
        # Start the FastAPI server for OAuth flow
        server_task = asyncio.create_task(
            run_server(settings.server.host, settings.server.port)
        )

        try:
            # Example of OAuth2 flow
            discord = DiscordClient(
                config=settings.discord
            )  # Initialize without token for OAuth2 flow

            # Define required scopes
            scopes = [
                "identify",
                "guilds",
                "guilds.members.read",
                "messages.read",
            ]

            # Get authorization URL
            auth_url = discord.get_authorization_url(scopes)
            print(
                f"OAuth server running at http://{settings.server.host}:{settings.server.port}"
            )
            print(f"Opening authorization URL in browser: {auth_url}")

            # Open the authorization URL in the default browser
            webbrowser.open(auth_url)

            # Wait for token to be saved
            print("Waiting for authentication...")
            while True:
                token_manager._load_tokens()
                latest_token = token_manager.get_latest_token()
                if latest_token and not latest_token.is_expired():
                    print("Authentication successful!")
                    discord = DiscordClient(
                        token=latest_token.access_token, token_type=TokenType.USER
                    )
                    break
                await sleep(1)

            # Cancel the server task since we don't need it anymore
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                pass
        except Exception as e:
            print(f"Error during OAuth flow: {e}")
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                pass
            sys.exit(1)

    try:
        # Print user guilds and messages
        guilds = await discord.get_current_user_guilds()
        print(f"Found {len(guilds)} guilds {guilds}")

        if guilds:
            for guild in guilds:
                print(f"Getting channels for guild: {guild.name}")
                try:
                    channels = await discord.get_guild_channels(guild.id)
                    text_channels = [
                        channel for channel in channels if channel.type == 0
                    ]

                    for channel in text_channels:
                        print(f"Getting messages from channel: {channel.name}")
                        try:
                            messages = await discord.get_channel_messages(
                                channel.id, limit=10
                            )

                            for message in messages:
                                print(f"Message ID: {message.id}")
                                print(f"{message.author.username}: {message.content}")
                                if message.attachments:
                                    print(f"  Attachments: {len(message.attachments)}")
                                if message.reactions:
                                    print(f"  Reactions: {len(message.reactions)}")
                                    print(f"  Sent at: {message.timestamp}")
                                    print("---")
                        except Exception as e:
                            print(
                                f"Error fetching messages from channel {channel.name}: {e}"
                            )
                except Exception as e:
                    print(f"Error fetching channels for guild {guild.name}: {e}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        await discord.close()


async def async_main_bot_flow() -> None:
    """Async main function for the bot flow with RAG-based message querying."""
    message_service = MessageService()

    try:
        print(f"{Fore.CYAN}Fetching messages from Discord...{Style.RESET_ALL}")
        await message_service.fetch_messages()

        print(f"{Fore.CYAN}Processing messages for RAG...{Style.RESET_ALL}")
        await message_service.process_messages()

        min_score = float(
            input(
                f"{Fore.YELLOW}Enter minimum similarity score threshold (0.0 to 1.0): {Style.RESET_ALL}"
            )
        )
        while min_score < 0.0 or min_score > 1.0:
            print(f"{Fore.RED}Score must be between 0.0 and 1.0{Style.RESET_ALL}")
            min_score = float(
                input(
                    f"{Fore.YELLOW}Enter minimum similarity score threshold (0.0 to 1.0): {Style.RESET_ALL}"
                )
            )

        # Interactive query loop
        while True:
            query = input(
                f"{Fore.CYAN}Enter a query (or 'exit' to quit): {Style.RESET_ALL}"
            )
            if query.lower() == "exit":
                break

            results = await message_service.query_messages(
                query, min_score=min_score, top_k=10
            )

            print(f"\n{Fore.CYAN}Query:{Style.RESET_ALL} {query}")
            print(f"\n{Fore.CYAN}Results:{Style.RESET_ALL}")
            for i, result in enumerate(results, 1):
                print(f"\n{Fore.YELLOW}--- Result {i} ---{Style.RESET_ALL}")
                print(f"{Fore.GREEN}Text:{Style.RESET_ALL} {result['text']}")
                print(f"{Fore.GREEN}Score:{Style.RESET_ALL} {result['score']:.4f}")
                print(
                    f"{Fore.GREEN}Author:{Style.RESET_ALL} {result['metadata']['author']}"
                )
                print(
                    f"{Fore.GREEN}Timestamp:{Style.RESET_ALL} {result['metadata']['timestamp']}"
                )
            print("\n\n---")
    finally:
        await message_service.close()


def main() -> None:
    """Synchronous entry point that runs the async main function."""
    try:
        asyncio.run(async_main_bot_flow())
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

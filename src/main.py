# -*- coding: utf-8 -*-
"""Main entry point for the discord-qna-bot CLI."""

import asyncio
import sys
import webbrowser
from asyncio import sleep
from typing import Optional

import httpx
import uvicorn
from colorama import Fore, Style

from .client.discord_api import DiscordAPI, TokenType
from .config import Config
from .dependencies import discord_client
from .oauth_server import app
from .rag_llama_index_faiss import MessageProcessor
from .token_storage import TokenStorage


async def run_server(host: str, port: int):
    """Run the FastAPI server using uvicorn"""
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def async_main_user_flow():
    """Async main function that contains the main logic"""
    # Load configuration
    config = Config()
    
    # Initialize token storage
    token_storage = TokenStorage()
    
    # Check for existing token
    latest_token = token_storage.get_latest_token()
    if latest_token and not latest_token.is_expired():
        print("Using existing token...")
        discord = DiscordAPI(token=latest_token.access_token, token_type=TokenType.USER)
    else:
        # Start the FastAPI server for OAuth flow
        server_task = asyncio.create_task(
            run_server(config.server.host, config.server.port)
        )
        
        try:
            # Example of OAuth2 flow
            discord = discord_client(config.discord)  # Initialize without token for OAuth2 flow
            
            # Define required scopes
            scopes = [
                "identify",
                "guilds",
                "guilds.members.read",
                "messages.read",
            ]
            
            # Get authorization URL
            auth_url = discord.get_authorization_url(scopes)
            print(f"OAuth server running at http://{config.server.host}:{config.server.port}")
            print(f"Opening authorization URL in browser: {auth_url}")
            
            # Open the authorization URL in the default browser
            webbrowser.open(auth_url)
            
            # Wait for token to be saved
            print("Waiting for authentication...")
            while True:
                token_storage._load_tokens()
                latest_token = token_storage.get_latest_token()
                if latest_token and not latest_token.is_expired():
                    print("Authentication successful!")
                    discord = DiscordAPI(token=latest_token.access_token, token_type=TokenType.USER)
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
        await fetch_and_print_messages(discord)
    except httpx.HTTPError as e:
        print(f"An HTTP error occurred: {e}")
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        await discord.close()
            
    
async def fetch_and_print_messages(discord: DiscordAPI):
    """Fetch and print messages from the Discord API"""
    # Get all guilds for the current user
    guilds = await discord.get_current_user_guilds()
    print(f"Found {len(guilds)} guilds {guilds}")
    if not guilds:
        print("No guilds found")
        return
    
    test_guild_name = "Test Guild 1"
    if test_guild_name not in [guild.name for guild in guilds]:
        guild = await discord.create_guild("Test Guild 1")
        print(f"Created guild: {guild}")
    else:
        guild = next(guild for guild in guilds if guild.name == test_guild_name)
        print(f"Using existing guild: {guild}")

    channels = []
    # Get first guild's ID
    print(f"Getting channels for guild: {guild.name}")
    try:
        # Get all channels for the first guild
        channels = await discord.get_guild_channels(guild.id)
        if not channels:
            print("No channels found")
            return
    except Exception as e:
        print(f"Error fetching channels for guild {guild.name}: {e}")

    # Find first text channel (type 0 is text channel)
    text_channels = [channel for channel in channels if channel.type == 0]
    print(f"Found {len(text_channels)} text channels {text_channels}")
    if not text_channels:
        print("No text channels found")
        return
    for channel in text_channels:
        print(f"Getting messages from channel: {channel.name}")
        
        try:
            # Get messages from the first text channel
            messages = await discord.get_channel_messages(
                channel.id,
                limit=10  # Get last 10 messages
            )
        
            # Print messages with proper formatting
            for message in messages:
                print(f"Message ID: {message}")
                print(f"{message.author.username}: {message.content}")
                if message.attachments:
                    print(f"  Attachments: {len(message.attachments)}")
                if message.reactions:
                    print(f"  Reactions: {len(message.reactions)}")
                    print(f"  Sent at: {message.timestamp}")
                    print("---")
        except Exception as e:
            print(f"Error fetching messages from channel {channel.name}: {e}")

async def async_main_bot_flow():
    """Async main function that contains the main logic"""
    config = Config()
    discord = DiscordAPI(token=config.discord.bot_token, token_type=TokenType.BOT)
    guilds = await discord.get_current_user_guilds()
    
    if not guilds:
        print(f"{Fore.RED}No guilds found{Style.RESET_ALL}")
        return
    channels = []
    for guild in guilds:
        print(f"\n{Fore.BLUE}=== Processing Guild: {guild.name} (ID: {guild.id}) ==={Style.RESET_ALL}")
        try:
            channels = await discord.get_guild_channels(guild.id)
            if not channels:
                print(f"{Fore.RED}No channels found{Style.RESET_ALL}")
                return
        except Exception as e:
            print(f"{Fore.RED}Error fetching channels for guild {guild.name}: {e}{Style.RESET_ALL}")

    channels = [channel for channel in channels if channel.type == 0]
    all_messages = []
    for channel in channels:
        print(f"\n{Fore.MAGENTA}=== Processing Channel: {channel.name} (ID: {channel.id}) ==={Style.RESET_ALL}")
        try:
            messages = await discord.get_channel_messages(channel.id)
            all_messages.extend(messages)
            print(f"\n{Fore.GREEN}=== Found {len(messages)} messages in channel {channel.name} ==={Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error fetching messages from channel {channel.name}: {e}{Style.RESET_ALL}")
    
    message_processor = MessageProcessor(all_messages)
    processed_data = message_processor.process_messages()
    index = message_processor.create_llama_index(processed_data)
    min_score = float(input(f"{Fore.YELLOW}Enter minimum similarity score threshold (0.0 to 1.0): {Style.RESET_ALL}"))
    while min_score < 0.0 or min_score > 1.0:
        print(f"{Fore.RED}Score must be between 0.0 and 1.0{Style.RESET_ALL}")
        min_score = float(input(f"{Fore.YELLOW}Enter minimum similarity score threshold (0.0 to 1.0): {Style.RESET_ALL}"))

    while True:
        query = input(f"{Fore.CYAN}Enter a query: {Style.RESET_ALL}")
        results = message_processor.query_discord_messages(index, query, top_k=10)

        print(f"\n{Fore.CYAN}Query:{Style.RESET_ALL} {query}")
        print(f"\n{Fore.CYAN}Results:{Style.RESET_ALL}")
        for i, result in enumerate(results, 1):
            if result['score'] >= min_score:
                print(f"\n{Fore.YELLOW}--- Result {i} ---{Style.RESET_ALL}")
                print(f"{Fore.GREEN}Text:{Style.RESET_ALL} {result['text']}")
                print(f"{Fore.GREEN}Score:{Style.RESET_ALL} {result['score']:.4f}")
                print(f"{Fore.GREEN}Author:{Style.RESET_ALL} {result['metadata']['author']}")
                print(f"{Fore.GREEN}Timestamp:{Style.RESET_ALL} {result['metadata']['timestamp']}")
        print("\n\n---")




def main():
    """Synchronous entry point that runs the async main function"""
    try:
        asyncio.run(async_main_bot_flow())
    except KeyboardInterrupt:
        print("\nShutting down...")
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

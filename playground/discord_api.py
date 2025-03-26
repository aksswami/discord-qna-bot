import asyncio
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel


# Pydantic Models
class EmojiModel(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None


class ReactionCountDetails(BaseModel):
    burst: int
    normal: int


class ReactionModel(BaseModel):
    count: int
    count_details: ReactionCountDetails
    me: bool
    me_burst: bool
    emoji: EmojiModel
    burst_colors: List[str]


class AuthorModel(BaseModel):
    username: str
    discriminator: str
    id: str
    avatar: Optional[str] = None


class MessageReferenceModel(BaseModel):
    type: int = 0
    channel_id: str
    message_id: str
    guild_id: Optional[str] = None


class MessageModel(BaseModel):
    id: str
    content: str
    channel_id: str
    author: AuthorModel
    timestamp: datetime
    edited_timestamp: Optional[datetime] = None
    tts: bool
    mention_everyone: bool
    mentions: List[Dict[str, Any]] = []
    mention_roles: List[str] = []
    attachments: List[Dict[str, Any]] = []
    embeds: List[Dict[str, Any]] = []
    reactions: Optional[List[ReactionModel]] = None
    pinned: bool
    type: int
    message_reference: Optional[MessageReferenceModel] = None
    referenced_message: Optional["MessageModel"] = None
    position: Optional[int] = None
    flags: Optional[int] = None
    components: List[Dict[str, Any]] = []


class ChannelModel(BaseModel):
    id: str
    guild_id: Optional[str] = None
    name: str
    type: int
    position: Optional[int] = None
    permission_overwrites: List[Dict[str, Any]] = []
    rate_limit_per_user: Optional[int] = None
    nsfw: Optional[bool] = None
    topic: Optional[str] = None
    last_message_id: Optional[str] = None
    parent_id: Optional[str] = None
    default_auto_archive_duration: Optional[int] = None


class GuildModel(BaseModel):
    id: str
    name: str
    icon: Optional[str] = None
    banner: Optional[str] = None
    owner: Optional[bool] = None
    permissions: Optional[str] = None
    features: List[str] = []
    approximate_member_count: Optional[int] = None
    approximate_presence_count: Optional[int] = None


class DiscordAPI:
    def __init__(self, api_token: str):
        self.api_base = "https://discord.com/api/v10"
        self.headers = {
            "Authorization": f"Bot {api_token}",
            "Content-Type": "application/json",
        }
        self.client = httpx.AsyncClient(headers=self.headers, timeout=30.0)

    async def close(self):
        """Close the HTTP client session"""
        await self.client.aclose()

    async def get_current_user_guilds(self) -> List[GuildModel]:
        """Get guilds (servers) for the current user"""
        response = await self.client.get(f"{self.api_base}/users/@me/guilds")
        response.raise_for_status()
        return [GuildModel(**guild) for guild in response.json()]

    async def get_guild_channels(self, guild_id: str) -> List[ChannelModel]:
        """Get channels for a specific guild"""
        response = await self.client.get(f"{self.api_base}/guilds/{guild_id}/channels")
        response.raise_for_status()
        return [ChannelModel(**channel) for channel in response.json()]

    async def get_channel_messages(
        self,
        channel_id: str,
        limit: int = 50,
        before: Optional[str] = None,
        after: Optional[str] = None,
        around: Optional[str] = None,
    ) -> List[MessageModel]:
        """Get messages from a specific channel with pagination support"""
        params = {"limit": min(limit, 100)}  # Discord's max limit is 100

        # Only one of these parameters can be used at a time
        if before:
            params["before"] = before
        elif after:
            params["after"] = after
        elif around:
            params["around"] = around

        response = await self.client.get(
            f"{self.api_base}/channels/{channel_id}/messages", params=params
        )
        response.raise_for_status()
        return [MessageModel(**message) for message in response.json()]


async def main() -> List[MessageModel]:
    # Replace with your bot token
    # application_id = "1354293773743427744"
    # public_key = "bd841f4c74d517c635df6f3e2fd4ea5677b7bfa38b1be476abb69b4a8af222ac"
    api_token = os.getenv("DISCORD_BOT_TOKEN")
    discord = DiscordAPI(api_token)

    try:
        # Get all guilds for the current user
        guilds = await discord.get_current_user_guilds()
        if not guilds:
            print("No guilds found")
            return

        # Get first guild's ID
        first_guild = guilds[0]
        print(f"Getting channels for guild: {first_guild.name}")

        # Get all channels for the first guild
        channels = await discord.get_guild_channels(first_guild.id)
        if not channels:
            print("No channels found")
            return

        # Find first text channel (type 0 is text channel)
        text_channel = next(
            (channel for channel in channels if channel.type == 0), None
        )
        if not text_channel:
            print("No text channels found")
            return

        print(f"Getting messages from channel: {text_channel.name}")

        # Get messages from the first text channel
        messages = await discord.get_channel_messages(
            text_channel.id, limit=10  # Get last 10 messages
        )

        # Print messages with proper formatting
        for message in messages:
            print(f"{message.author.username}: {message.content}")
            if message.attachments:
                print(f"  Attachments: {len(message.attachments)}")
            if message.reactions:
                print(f"  Reactions: {len(message.reactions)}")
            print(f"  Sent at: {message.timestamp}")
            print("---")
        return messages

    except httpx.HTTPError as e:
        print(f"An HTTP error occurred: {e}")
    finally:
        await discord.close()


if __name__ == "__main__":
    messages = asyncio.run(main())

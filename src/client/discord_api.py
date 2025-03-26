import asyncio
import webbrowser
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field

from ..config import DiscordConfig


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

class TokenType(Enum):
    BOT = "Bot"
    USER = "User"

class OAuth2TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str
    scope: str

class DiscordAPI:
    def __init__(self, config: DiscordConfig | None = None, token: str | None = None, token_type: TokenType = TokenType.BOT):
        self.api_base = "https://discord.com/api/v10"
        self.oauth_base = "https://discord.com/oauth2"
        self.client_id = config.client_id if config else None
        self.client_secret = config.client_secret if config else None
        self.redirect_uri = config.redirect_uri if config else None
        if token:
            self.headers = {
                "Authorization": f"{'Bot' if token_type == TokenType.BOT else 'Bearer'} {token}",
                "Content-Type": "application/json"
            }
        else:
            self.headers = {
                "Content-Type": "application/json"
            }   
        self.client = httpx.AsyncClient(headers=self.headers, timeout=30.0)

    @classmethod
    async def exchange_code_for_token(cls, code: str, config: DiscordConfig) -> OAuth2TokenResponse:
        """Exchange authorization code for access token"""
        data = {
            'client_id': config.client_id,
            'client_secret': config.client_secret,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': config.redirect_uri
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'https://discord.com/api/v10/oauth2/token',
                data=data
            )
            response.raise_for_status()
            return OAuth2TokenResponse(**response.json())

    def get_authorization_url(self, scopes: List[str]) -> str:
        """Generate authorization URL for OAuth2 flow"""
        scope_string = ' '.join(scopes)
        return (
            f"{self.oauth_base}/authorize"
            f"?client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&response_type=code"
            f"&scope={scope_string}"
        )

    async def close(self):
        """Close the HTTP client session"""
        await self.client.aclose()

    async def get_current_user_guilds(self) -> List[GuildModel]:
        """Get guilds (servers) for the current user"""
        response = await self.client.get(f"{self.api_base}/users/@me/guilds")
        response.raise_for_status()
        return [GuildModel(**guild) for guild in response.json()]
    
    async def create_guild(self, name: str, icon: Optional[str] = None) -> GuildModel:
        """Create a new guild (server)
        
        Args:
            name: Name of the guild (2-100 characters)
            icon: Optional base64 128x128 image for the guild icon
            
        Returns:
            GuildModel object representing the created guild
            
        Note:
            This endpoint can only be used by bots in less than 10 guilds
        """
        payload = {
            "name": name
        }
        if icon:
            payload["icon"] = icon
            
        response = await self.client.post(
            f"{self.api_base}/guilds",
            json=payload
        )
        response.raise_for_status()
        return GuildModel(**response.json())

    async def get_guild_channels(self, guild_id: str) -> List[ChannelModel]:
        """Get channels for a specific guild"""
        response = await self.client.get(
            f"{self.api_base}/guilds/{guild_id}/channels"
        )
        response.raise_for_status()
        return [ChannelModel(**channel) for channel in response.json()]

    async def get_channel_messages(
        self, 
        channel_id: str, 
        limit: int = 50,
        before: Optional[str] = None,
        after: Optional[str] = None,
        around: Optional[str] = None
    ) -> List[MessageModel]:
        """Get messages from a specific channel with pagination support"""
        params = {'limit': min(limit, 100)}  # Discord's max limit is 100
        
        # Only one of these parameters can be used at a time
        if before:
            params['before'] = before
        elif after:
            params['after'] = after
        elif around:
            params['around'] = around

        response = await self.client.get(
            f"{self.api_base}/channels/{channel_id}/messages",
            params=params
        )
        response.raise_for_status()
        return [MessageModel(**message) for message in response.json()]

async def main():
    # Replace with your bot token
    # application_id = "1354293773743427744"
    # public_key = "bd841f4c74d517c635df6f3e2fd4ea5677b7bfa38b1be476abb69b4a8af222ac"
    # api_token = os.getenv("DISCORD_BOT_TOKEN")
    # print(f"API Token: {api_token}")
    # discord = DiscordAPI(api_token)

    # try:
    #     # Get all guilds for the current user
    #     guilds = await discord.get_current_user_guilds()
    #     if not guilds:
    #         print("No guilds found")
    #         return

    #     # Get first guild's ID
    #     first_guild = guilds[0]
    #     print(f"Getting channels for guild: {first_guild.name}")

    #     # Get all channels for the first guild
    #     channels = await discord.get_guild_channels(first_guild.id)
    #     if not channels:
    #         print("No channels found")
    #         return

    #     # Find first text channel (type 0 is text channel)
    #     text_channel = next((channel for channel in channels if channel.type == 0), None)
    #     if not text_channel:
    #         print("No text channels found")
    #         return

    #     print(f"Getting messages from channel: {text_channel.name}")
        
    #     # Get messages from the first text channel
    #     messages = await discord.get_channel_messages(
    #         text_channel.id,
    #         limit=10  # Get last 10 messages
    #     )
        
    #     # Print messages with proper formatting
    #     for message in messages:
    #         print(f"Message ID: {message}")
    #         print(f"{message.author.username}: {message.content}")
    #         if message.attachments:
    #             print(f"  Attachments: {len(message.attachments)}")
    #         if message.reactions:
    #             print(f"  Reactions: {len(message.reactions)}")
    #         print(f"  Sent at: {message.timestamp}")
    #         print("---")

    # except httpx.HTTPError as e:
    #     print(f"An HTTP error occurred: {e}")
    # finally:
    #     await discord.close()


    # Example of OAuth2 flow
    discord = DiscordAPI()  # Initialize without token for OAuth2 flow
    
    # Define required scopes
    scopes = [
        "identify",
        "guilds",
        "guilds.members.read",
        "messages.read"
    ]
    
    # Get authorization URL
    auth_url = discord.get_authorization_url(scopes)
    print(f"Please visit this URL to authorize: {str(auth_url)}")
    webbrowser.open(auth_url)
    
    # After user visits the URL and authorizes, they will be redirected to your redirect_uri
    # with a code parameter. You would typically handle this in your web application.
    
    # Example of exchanging the code for a token
    # code = "received_code_from_redirect"
    # token_response = await DiscordAPI.exchange_code_for_token(code)
    # print(f"Access Token: {token_response.access_token}")
    
    # Now you can create a new DiscordAPI instance with the access token
    # discord = DiscordAPI(token_response.access_token, TokenType.USER)
    
    # Rest of your code...

if __name__ == "__main__":
    asyncio.run(main())

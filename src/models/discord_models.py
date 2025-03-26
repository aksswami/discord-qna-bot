"""Discord data models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


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

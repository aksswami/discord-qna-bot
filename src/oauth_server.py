import asyncio
from datetime import datetime, timedelta
from typing import Optional

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse

from .client.discord_api import DiscordAPI
from .config import ServerConfig, config
from .dependencies import discord_client
from .token_storage import TokenData, TokenStorage

app = FastAPI(title="Discord OAuth Server")
app.dependency_overrides[discord_client] = lambda: discord_client(config.discord)

# Initialize token storage
token_storage = TokenStorage()

@app.get("/")
async def root():
    return {"message": "Discord OAuth Server is running"}

@app.get("/auth", dependencies=[Depends(discord_client)])
async def auth():
    """Redirect to Discord OAuth authorization page"""
    auth_url = discord_client.get_authorization_url(
        scopes=["identify", "guilds", "messages.read"]
    )
    return RedirectResponse(url=auth_url)

@app.get("/oauth2/callback", dependencies=[Depends(discord_client)])
async def callback(code: str, state: Optional[str] = None):
    """Handle the OAuth callback from Discord"""
    try:
        print(f"Received code from callback: {code}")
        # Exchange the code for a token
        token_response = await DiscordAPI.exchange_code_for_token(code, config=config.discord)
        token_data = TokenData(
            access_token=token_response.access_token,
            token_type=token_response.token_type,
            expires_in=token_response.expires_in,
            refresh_token=token_response.refresh_token,
            scope=token_response.scope,
            expires_at=datetime.utcnow() + timedelta(seconds=token_response.expires_in)
        )
        
        # Save the token
        token_id = str(len(token_storage._tokens) + 1)
        token_storage.save_token(token_id, token_data)
        
        # Redirect to a success page or your main application
        return {
            "message": "Authentication successful",
            "token_id": token_id,
            "access_token": token_response.access_token,
            "token_type": token_response.token_type,
            "expires_in": token_response.expires_in,
            "refresh_token": token_response.refresh_token,
            "scope": token_response.scope
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error during OAuth flow: {str(e)}")

def start_server(host: str = None, port: int = None, server_config: ServerConfig = None):
    """Start the FastAPI server"""
    # Use provided values or fall back to settings
    host = host or server_config.host
    port = port or server_config.port
    
    uvicorn.run(app, host=host, port=port)

import os
from typing import Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
import uvicorn
import asyncio
from urllib.parse import urlencode

from playground.discord_api import DiscordAPI, OAuth2TokenResponse

app = FastAPI(title="Discord OAuth Server")

# Store tokens temporarily (in a real app, use a proper database)
tokens: dict[str, OAuth2TokenResponse] = {}

@app.get("/")
async def root():
    return {"message": "Discord OAuth Server is running"}

@app.get("/auth")
async def auth():
    """Redirect to Discord OAuth authorization page"""
    discord_api = DiscordAPI()
    auth_url = discord_api.get_authorization_url(
        scopes=["identify", "guilds", "messages.read"]
    )
    return RedirectResponse(url=auth_url)

@app.get("/callback")
async def callback(code: str, state: Optional[str] = None):
    """Handle the OAuth callback from Discord"""
    try:
        # Exchange the code for a token
        token_response = await DiscordAPI.exchange_code_for_token(code)
        
        # In a real application, you would store this token securely
        # For demo purposes, we'll just store it in memory with a simple ID
        token_id = str(len(tokens) + 1)
        tokens[token_id] = token_response
        
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

def start_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the FastAPI server"""
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start_server()

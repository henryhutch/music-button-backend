from datetime import datetime, timedelta
from fastapi import HTTPException
from app.models import User
from sqlmodel import Session
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")


def get_valid_token(user: User, session: Session) -> str:
    if datetime.utcnow() < user.token_expiry:
        return user.access_token

    resp = httpx.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": user.refresh_token,
            "client_id": SPOTIFY_CLIENT_ID,
            "client_secret": SPOTIFY_CLIENT_SECRET
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    data = resp.json()
    if "access_token" not in data:
        raise HTTPException(status_code=400, detail="Failed to refresh token.")

    user.access_token = data["access_token"]
    user.token_expiry = datetime.utcnow() + timedelta(seconds=data["expires_in"])
    session.add(user)
    session.commit()
    return user.access_token

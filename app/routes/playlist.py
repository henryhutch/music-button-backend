from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.auth.sessions import get_current_user
from app.db import get_session
from app.models import User
import httpx

router = APIRouter(prefix="/api/playlist")


@router.get("/", summary="Get or create the user's playlist")
def get_or_create_playlist(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if user.playlist_id:
        return {"playlist_id": user.playlist_id}

    # Create a new playlist on Spotify
    headers = {
        "Authorization": f"Bearer {user.access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "name": "ESP32 Music Button",
        "description": "Songs added from my ESP32 button!",
        "public": False
    }

    resp = httpx.post(
        f"https://api.spotify.com/v1/users/{user.user_id}/playlists",
        json=payload,
        headers=headers
    )

    if resp.status_code != 201:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Spotify error: {resp.json()}"
        )

    playlist_data = resp.json()
    playlist_id = playlist_data["id"]

    # Store playlist_id in the user object
    user.playlist_id = playlist_id
    session.add(user)
    session.commit()

    return {"playlist_id": playlist_id}

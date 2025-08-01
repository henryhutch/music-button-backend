from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlmodel import Session, select
from app.db import get_session
from app.models import Button, User, RecentSong
from app.auth.oauth import get_valid_token
from app.auth.sessions import get_current_user
import httpx
import os
from typing import List
from dotenv import load_dotenv
import shutil
from pathlib import Path
from datetime import datetime

load_dotenv()

AUDD_API_TOKEN = os.getenv("AUDD_API_TOKEN")

router = APIRouter(
    prefix="/api",
    tags=["Song"]
)


def extract_track_id(url_or_uri: str) -> str:
    if "spotify:track:" in url_or_uri:
        return url_or_uri.split("spotify:track:")[-1]
    elif "open.spotify.com/track/" in url_or_uri:
        return url_or_uri.split("track/")[-1].split("?")[0]
    elif len(url_or_uri) == 22:  # Just the ID
        return url_or_uri
    else:
        raise ValueError("Invalid Spotify track input")


def enhance_song_info(track_id: str, user: User, session: Session):
    api_token = get_valid_token(user, session)

    track_resp = httpx.get(
        f"https://api.spotify.com/v1/tracks/{track_id}",
        headers={"Authorization": f"Bearer {api_token}"}
    )

    track_resp.raise_for_status()
    track = track_resp.json()

    return track


def identify_song(upload_file: UploadFile):
    files = {
        'file': (upload_file.filename, upload_file.file, 'audio/wav')
    }

    data = {
        'api_token': AUDD_API_TOKEN,
        'return': 'spotify'
    }

    response = httpx.post('https://api.audd.io/', data=data, files=files)

    try:
        result = response.json()
    except ValueError:
        raise HTTPException(status_code=500, detail="AudD returned an invalid response.")

    return result


def add_to_spotify(track_id: str, user: User, session: Session):

    api_token = get_valid_token(user, session)

    print(track_id)
    print(api_token)

    if not user.playlist_id:
        resp = httpx.post(
            f"https://api.spotify.com/v1/users/{user.user_id}/playlists",
            headers={"Authorization": f"Bearer {api_token}"},
            json={"name": "Music Button", "public": False},
        )
        playlist_data = resp.json()
        user.playlist_id = playlist_data["id"]
        session.add(user)
        session.commit()

        print("playlist created.")

    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }

    add_url = f"https://api.spotify.com/v1/playlists/{user.playlist_id}/tracks"

    data = {
        'uris': [f'spotify:track:{track_id}'],
        'position': 0
    }

    resp = httpx.post(url=add_url, headers=headers, json=data)

    # Raise if it failed
    resp.raise_for_status()

    return {"status": "song added."}


@router.post("/upload")
def upload(button_id: str, file: UploadFile = File(...), session: Session = Depends(get_session)):
    try:

        # 1. Save file to disk for debugging
        save_dir = Path("recordings")
        save_dir.mkdir(exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        save_path = save_dir / f"{button_id}_{timestamp}.wav"

        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file.file.seek(0)  # Reset stream for further processing

        result = identify_song(file)
        if result.get("status") != "success" or not result.get("result"):
            return {"success": False, "reason": "No match found."}

        song_info = result["result"]
        spotify_url = song_info["spotify"]["external_urls"]["spotify"]
        track_id = extract_track_id(spotify_url)

        button = session.get(Button, button_id)
        if not button:
            raise HTTPException(status_code=404, detail="Button not registered.")

        user = session.get(User, button.user_id)

        added = add_to_spotify(track_id, user, session)

        if not added:
            return {"success": False, "reason": "Spotify add failed."}

        track_info = enhance_song_info(track_id, user, session)

        recent = RecentSong(
            user_id=user.user_id,
            track_id=track_id,
            track_name=track_info["name"],
            artist=", ".join([a["name"] for a in track_info["artists"]]),
            album=track_info["album"]["name"],
            image_url=track_info["album"]["images"][0]["url"] if track_info["album"]["images"] else None
        )
        session.add(recent)
        session.commit()

        return {
            "success": True
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/recent")
def get_recent_songs(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    return session.exec(
        select(RecentSong)
        .where(RecentSong.user_id == user.user_id)
        .order_by(RecentSong.__table__.c.added_at.desc())
        .limit(10)
    ).all()

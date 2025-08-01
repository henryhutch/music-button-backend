import base64
import hashlib
import secrets
import os
import urllib.parse
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlmodel import Session, select
from dotenv import load_dotenv

from app.db import get_session
from app.models import User
from app.auth.sessions import get_current_user, session_store

load_dotenv()
router = APIRouter(
    prefix="/api/auth",
    tags=["Auth"]
)

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
SPOTIFY_SCOPES = "playlist-modify-private playlist-read-private user-read-private"

PKCE_STORE = {}


def generate_code_verifier() -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()


def generate_code_challenge(verifier: str) -> str:
    sha256 = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(sha256).rstrip(b"=").decode()


@router.get("/check")
def check_auth(current_user: User = Depends(get_current_user)):
    return {"user_id": current_user.user_id}


@router.get("/spotify")
def auth():
    state = secrets.token_urlsafe(16)
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)
    PKCE_STORE[state] = code_verifier

    params = {
        "client_id": SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "scope": SPOTIFY_SCOPES,
        "state": state,
        "code_challenge_method": "S256",
        "code_challenge": code_challenge,
    }
    url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(params)
    return RedirectResponse(url)


@router.get("/post-auth", response_class=HTMLResponse)
def post_auth_redirect():
    return """
    <html>
      <head>
        <meta http-equiv="refresh" content="0;url='https://music-button.henryhutchison.com'" />
      </head>
      <body>
        Auth successful. Redirecting to app...
      </body>
    </html>
    """

@router.get("/callback")
def callback(request: Request, session: Session = Depends(get_session)):
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    error = request.query_params.get("error")

    if error:
        raise HTTPException(status_code=400, detail=f"Spotify auth error: {error}")

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state")

    code_verifier = PKCE_STORE.pop(state, None)
    if not code_verifier:
        raise HTTPException(status_code=400, detail="Invalid state")

    import httpx

    token_resp = httpx.post(
        "https://accounts.spotify.com/api/token",
        data={
            "client_id": SPOTIFY_CLIENT_ID,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": SPOTIFY_REDIRECT_URI,
            "code_verifier": code_verifier,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    token_resp.raise_for_status()
    token_data = token_resp.json()

    access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]
    expires_in = token_data["expires_in"]

    user_resp = httpx.get(
        "https://api.spotify.com/v1/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    user_resp.raise_for_status()
    user_data = user_resp.json()

    user_id = user_data["id"]

    user = session.get(User, user_id)
    expiry = datetime.utcnow() + timedelta(seconds=expires_in)

    if not user:
        user = User(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expiry=expiry,
            playlist_id=None
        )
        session.add(user)

    else:
        user.access_token = access_token
        user.refresh_token = refresh_token
        user.token_expiry = expiry

    session.commit()

    session_id = str(uuid.uuid4())
    session_store[session_id] = user_id

    response = RedirectResponse(url="/api/auth/post-auth")

    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=True,  # ✅ Must be True
        samesite="None",  # ✅ Required for cross-site cookies
        max_age=60 * 60 * 24 * 7,
        path="/"
    )

    return response

@router.post("/logout")
def logout(request: Request, response: Response):
    session_id = request.cookies.get("session_id")

    # Clear from session store (if using in-memory sessions)
    if session_id:
        session_store.pop(session_id, None)

    # Delete the cookie
    response.delete_cookie(
        key="session_id",
        path="/",  # Make sure this matches the original cookie path
    )

    return {"detail": "Logged out successfully"}


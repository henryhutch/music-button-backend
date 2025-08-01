from typing import List, Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship


class User(SQLModel, table=True):
    user_id: str = Field(primary_key=True)
    access_token: str
    refresh_token: str
    token_expiry: datetime
    playlist_id: Optional[str] = None

    registered_buttons: List["Button"] = Relationship(back_populates="user")


class Button(SQLModel, table=True):
    button_id: str = Field(primary_key=True)
    user_id: str = Field(foreign_key="user.user_id")
    user: Optional[User] = Relationship(back_populates="registered_buttons")


class RecentSong(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="user.user_id")
    track_id: str
    added_at: datetime = Field(default_factory=datetime.utcnow)

    track_name: str | None = None
    artist: str | None = None
    album: str | None = None
    image_url: str | None = None

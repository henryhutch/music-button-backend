from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class ButtonRegisterRequest(BaseModel):
    button_id: str
    user_id: str


class ButtonResponse(BaseModel):
    button_id: str
    user_id: str

    class Config:
        orm_mode = True


class RecentSongRead(BaseModel):
    id: int
    user_id: str
    track_id: str
    added_at: datetime
    track_name: Optional[str]
    artist: Optional[str]
    album: Optional[str]
    image_url: Optional[str]

    class Config:
        orm_mode = True

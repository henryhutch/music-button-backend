from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.auth.sessions import get_current_user
from app.db import get_session
from app.models import User, Button
from app.schemas import ButtonRegisterRequest, ButtonResponse

router = APIRouter(
    prefix="/api/button",
    tags=["Button"]
)


@router.get("/", response_model=list[ButtonResponse])
def get_user_buttons(current_user: User = Depends(get_current_user)):
    return current_user.registered_buttons


@router.post("/", response_model=dict)
def register_button(data: ButtonRegisterRequest, session: Session = Depends(get_session)):

    user = session.get(User, data.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    button = Button(button_id=data.button_id, user_id=data.user_id)
    session.add(button)
    session.commit()
    return {"status": "registered"}

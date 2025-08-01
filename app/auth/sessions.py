from fastapi import Request, Depends, HTTPException, status
from sqlmodel import Session, select
from app.models import User
from app.db import get_session

# Temporary in-memory session store
session_store = {}


def get_current_user(
    request: Request,
    db: Session = Depends(get_session)
) -> User:
    session_id = request.cookies.get("session_id")
    print(session_id)
    print(session_store)
    if not session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No session cookie")

    user_id = session_store.get(session_id)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    user = db.exec(select(User).where(User.user_id == user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user

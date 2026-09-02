from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import User

security = HTTPBearer(auto_error=False)

DEMO_USERS = [
    {"username": "citizen", "password": "demo123", "role": "citizen", "display_name": "Community reporter", "district": "East Khasi Hills"},
    {"username": "field", "password": "demo123", "role": "field", "display_name": "Field official", "district": "East Khasi Hills"},
    {"username": "district", "password": "demo123", "role": "district", "display_name": "District Emergency Officer", "district": "East Khasi Hills"},
    {"username": "sdma", "password": "demo123", "role": "sdma", "display_name": "SDMA / NDMA watch desk", "district": "NER"},
]


def make_token(user: User) -> str:
    payload = {
        "sub": user.username,
        "role": user.role,
        "uid": user.id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=48),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if not creds:
        raise HTTPException(status_code=401, detail="Login required")
    data = decode_token(creds.credentials)
    user = db.query(User).filter(User.username == data.get("sub")).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def optional_user(
    creds: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User | None:
    if not creds:
        return None
    try:
        data = decode_token(creds.credentials)
    except HTTPException:
        return None
    return db.query(User).filter(User.username == data.get("sub")).first()


def require_roles(*roles: str):
    def _inner(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Not allowed for this role")
        return user

    return _inner

"""Connexion JSON et vérification des JWT pour les routes protégées."""

import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, field_validator
from sqlmodel import Session, select

from database import get_session, normalize_password_hash
from models import User

router = APIRouter(tags=["Authentification"])
bearer = HTTPBearer(auto_error=False)
TOKEN_DURATION = timedelta(hours=1)
# Même travail bcrypt pour un email inconnu : éviter une réponse plus rapide.
DUMMY_HASH = bcrypt.hashpw(b"unused-password", bcrypt.gensalt()).decode()


class LoginRequest(BaseModel):
    email: str = Field(max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    password: str = Field(min_length=1, max_length=72)

    @field_validator("password")
    @classmethod
    def check_password_size(cls, value):
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Mot de passe trop long.")
        return value


def jwt_secret():
    secret = os.getenv("JWT_SECRET_KEY", "")
    if len(secret.encode("utf-8")) < 32:
        raise HTTPException(503, "Authentification temporairement indisponible.")
    return secret


@router.post("/login")
def login(body: LoginRequest, response: Response, session: Session = Depends(get_session)):
    user = session.exec(
        select(User).where(User.email == body.email.strip().lower())
    ).first()
    stored_hash = user.hashed_password if user else DUMMY_HASH
    try:
        valid_password = bcrypt.checkpw(
            body.password.encode("utf-8"), normalize_password_hash(stored_hash).encode()
        )
    except (ValueError, TypeError, UnicodeError):
        valid_password = False
    if user is None or not valid_password:
        raise HTTPException(401, "Email ou mot de passe incorrect.")

    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {"sub": str(user.id), "iat": now, "exp": now + TOKEN_DURATION},
        jwt_secret(),
        algorithm="HS256",
    )
    response.headers["Cache-Control"] = "no-store"
    return {"access_token": token, "token_type": "bearer"}


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    session: Session = Depends(get_session),
):
    error = HTTPException(
        401, "Session invalide ou expirée.", headers={"WWW-Authenticate": "Bearer"}
    )
    if credentials is None:
        raise error
    try:
        payload = jwt.decode(
            credentials.credentials, jwt_secret(), algorithms=["HS256"],
            options={"require": ["sub", "exp"]},
        )
        user_id = int(payload["sub"])
        if not 0 < user_id <= 2**63 - 1:
            raise ValueError("Invalid user id")
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise error from None
    user = session.get(User, user_id)
    if user is None:
        raise error
    return user


@router.get("/me")
def me(response: Response, user: User = Depends(get_current_user)):
    response.headers["Cache-Control"] = "no-store"
    return {"id": user.id, "email": user.email}

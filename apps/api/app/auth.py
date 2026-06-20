import base64
import hashlib
import hmac
import secrets

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from packages.db import get_session
from packages.db.models import User, UserSession, UserTopicPreference
from packages.shared.config import Settings, get_settings


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_password(password: str, settings: Settings | None = None) -> str:
    config = settings or get_settings()
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        config.password_hash_iterations,
    )
    return (
        f"pbkdf2_sha256${config.password_hash_iterations}$"
        f"{base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"
    )


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations, salt, expected = password_hash.split("$", 3)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        base64.b64decode(salt),
        int(iterations),
    )
    return hmac.compare_digest(base64.b64encode(digest).decode(), expected)


def create_session(db: Session, user: User, settings: Settings | None = None) -> UserSession:
    config = settings or get_settings()
    session = UserSession(user_id=user.id, token=secrets.token_urlsafe(config.session_token_bytes))
    db.add(session)
    db.flush()
    return session


def ensure_topic_preferences(db: Session, user: User, settings: Settings | None = None) -> None:
    config = settings or get_settings()
    existing = {
        row.topic
        for row in db.query(UserTopicPreference).filter(UserTopicPreference.user_id == user.id).all()
    }
    for topic in config.topics:
        if topic not in existing:
            db.add(UserTopicPreference(user_id=user.id, topic=topic, enabled=True))


def current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_session),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Sign in to continue.")

    token = authorization.removeprefix("Bearer ").strip()
    session = db.query(UserSession).filter(UserSession.token == token).one_or_none()
    if session is None:
        raise HTTPException(status_code=401, detail="Session expired. Sign in again.")
    return session.user

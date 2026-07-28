"""
Security utilities: password hashing + JWT tokens.

--- Why hash passwords? ---
Imagine writing every user's password in a notebook in plain text.
If someone steals the notebook, they now have everyone's password.
"Hashing" runs the password through a one-way math function (bcrypt).
It's like putting a message through a shredder: easy to shred,
impossible to un-shred. When a user logs in, we shred their typed
password the same way and compare the shredded versions — never
the real ones.

--- Why JWT (JSON Web Token)? ---
After login, the server needs a way to recognize "this request
belongs to this logged-in user" WITHOUT asking for the password
on every single click. A JWT is like a wristband at a concert:
the bouncer (server) stamps it once at the door (login), and for
the rest of the night, showing the wristband is enough to prove
you belong inside. It's signed with a secret key so no one can
forge a fake wristband.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt

from app.core.config import settings


def hash_password(plain_password: str) -> str:
    """
    Runs the password through bcrypt's one-way hash function.
    bcrypt only looks at the first 72 bytes of input by design,
    so we truncate first to avoid an error on very long passwords.
    """
    password_bytes = plain_password.encode("utf-8")[:72]
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode("utf-8")[:72]
    return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))


def create_access_token(subject: str, role: str) -> str:
    """
    Creates the short-lived 'wristband' used for normal API calls.
    `subject` is usually the user's id; `role` lets the backend
    quickly check permissions without a database lookup on every call.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": subject, "role": role, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str) -> str:
    """
    Creates the long-lived token used ONLY to get a new access token
    when the short one expires — like a season pass you show only
    to renew your wristband, not to get into the show directly.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {"sub": subject, "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Raises jose.JWTError if the token is invalid, tampered, or expired."""
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
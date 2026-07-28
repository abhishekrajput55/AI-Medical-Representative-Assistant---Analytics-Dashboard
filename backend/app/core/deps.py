"""
Reusable "gatekeepers" (FastAPI dependencies).

`get_current_user` checks the wristband (JWT) on every protected
request. `require_role(...)` is a gate that only lets certain job
titles through — e.g. only Admins can delete a user.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User, UserRole

# HTTPBearer gives a simple "paste your token" box in Swagger's
# Authorize button — a better fit than OAuth2PasswordBearer, since
# our /login endpoint takes JSON, not an OAuth2 form.
bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_error
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_error
    except JWTError:
        raise credentials_error

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise credentials_error
    return user


def require_role(*allowed_roles: UserRole):
    """
    Usage in a router:
        @router.delete("/users/{id}", dependencies=[Depends(require_role(UserRole.ADMIN))])

    This is a "dependency factory" — a function that returns a
    function. It lets us reuse the same gate logic for any
    combination of allowed roles, on any endpoint.
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role.value}' is not permitted to perform this action.",
            )
        return current_user
    return role_checker
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    error = HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise error
    user = db.get(User, user_id)
    if not user:
        raise error
    request.state.user_id = user.id  # <-- new: the middleware reads this
    return user


def require_hr(user: User = Depends(get_current_user)) -> User:
    if user.role != "hr":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "HR access required")
    return user


# Its main responsibility is:
# 1. Extract the JWT token from an incoming request.
# 2. Verify that the token is valid.
# 3. Identify which user is making the request.
# 4. Check whether that user has permission to access a particular endpoint.

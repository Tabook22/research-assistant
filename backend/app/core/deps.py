"""FastAPI dependencies."""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database import get_db
from app.models.user import User

security = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    try:
        ident = int(payload['sub'])
    except (TypeError, ValueError):
        raise HTTPException(401, 'Invalid token')
    user = db.get(User, ident)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if payload.get('ver', 0) != user.auth_version:
        raise HTTPException(401, 'Your session has expired. Please sign in again.')
    path = request.url.path
    if user.must_change_password and not (path.endswith('/auth/me') or path.endswith('/auth/account')):
        raise HTTPException(403, 'Change your temporary password in Account settings before continuing.')
    from app.services.permissions import enforce
    enforce(user, path, request.method)
    return user

def get_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_superuser:
        raise HTTPException(403, 'Administrator access required.')
    return user

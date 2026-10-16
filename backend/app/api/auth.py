"""Authentication routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models.user import User
from app.schemas.auth import TokenOut, UserCreate, UserLogin, UserOut, AccountUpdate
from app.config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])

def session_for(user):
    return TokenOut(access_token=create_access_token(user.id, {'ver':user.auth_version}), user=UserOut.model_validate(user))

@router.get('/config')
def configuration():
    return {'allow_registration':get_settings().allow_registration}


@router.post("/register", response_model=TokenOut)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> TokenOut:
    if not get_settings().allow_registration:
        raise HTTPException(403, 'Accounts are created by your administrator. Contact the administrator for access.')
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        preferred_language=payload.preferred_language,
        username=payload.username,
    )
    db.add(user)
    try:db.commit()
    except IntegrityError:
        db.rollback();raise HTTPException(409,'Username or email is already in use.')
    db.refresh(user)
    return session_for(user)


@router.post("/login", response_model=TokenOut)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> TokenOut:
    ident=(payload.username or payload.email or '').strip().lower()
    user = db.query(User).filter(or_(User.email == ident,User.username == ident)).first()
    if not user or not user.is_active or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return session_for(user)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user

@router.get('/papers')
def my_papers(db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    from app.services.user_workspace import papers_for_user
    return papers_for_user(db,user)

@router.patch('/account',response_model=TokenOut)
def update_account(payload:AccountUpdate,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    if not verify_password(payload.current_password,user.hashed_password):
        raise HTTPException(400,'Current password is incorrect.')
    if user.must_change_password and not payload.new_password:
        raise HTTPException(400,'Set a new password to replace your temporary password.')
    if payload.new_password:
        if verify_password(payload.new_password,user.hashed_password):raise HTTPException(400,'Choose a different password.')
        user.hashed_password=hash_password(payload.new_password)
        user.must_change_password=False
    if payload.username is not None:user.username=payload.username
    if payload.full_name is not None:user.full_name=payload.full_name
    user.auth_version+=1
    try:db.commit()
    except IntegrityError:
        db.rollback();raise HTTPException(409,'Username is already in use.')
    db.refresh(user)
    return session_for(user)

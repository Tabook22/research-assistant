"""Auth schemas."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

def valid_password(value: str) -> str:
    if len(value.encode('utf-8')) > 72:
        raise ValueError('Password must be at most 72 UTF-8 bytes.')
    return value

def valid_username(value):
    if value is None:return None
    import re
    value=value.strip().lower()
    if not re.fullmatch(r'[a-z0-9_.-]{3,40}',value):
        raise ValueError('Username must be 3–40 letters, numbers, dots, underscores or hyphens.')
    return value


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    preferred_language: str = "en"
    username: str | None = None
    _username = field_validator('username')(valid_username)
    _password = field_validator('password')(valid_password)


class UserLogin(BaseModel):
    email: str | None = Field(default=None, max_length=255)
    username: str | None = Field(default=None, max_length=255)
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    preferred_language: str
    is_active: bool
    created_at: datetime
    username: str | None = None
    is_superuser: bool
    permissions: list[str]
    must_change_password: bool

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

class AccountUpdate(BaseModel):
    current_password: str
    username: str | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    new_password: str | None = Field(default=None, min_length=8, max_length=128)
    _username = field_validator('username')(valid_username)
    @field_validator('new_password')
    @classmethod
    def password_length(cls,value):return valid_password(value) if value is not None else value

class ManagedUserCreate(BaseModel):
    must_change_password: bool = False
    username: str
    full_name: str = Field(min_length=1,max_length=255)
    email: EmailStr | None = None
    password: str = Field(min_length=8,max_length=128)
    preferred_language: str = Field(default='en',pattern='^(en|ar)$')
    permissions: list[str] = Field(default_factory=list)
    is_superuser: bool = False
    _username = field_validator('username')(valid_username)
    _password = field_validator('password')(valid_password)
    @field_validator('permissions')
    @classmethod
    def grants(cls,value):
        from app.services.permissions import PERMISSIONS
        if set(value)-set(PERMISSIONS):raise ValueError('Unknown page permission.')
        return list(dict.fromkeys(value))

class ManagedUserUpdate(BaseModel):
    must_change_password: bool | None = None
    username: str | None = None
    full_name: str | None = Field(default=None,min_length=1,max_length=255)
    is_active: bool | None = None
    is_superuser: bool | None = None
    permissions: list[str] | None = None
    password: str | None = Field(default=None,min_length=8,max_length=128)
    _username = field_validator('username')(valid_username)
    @field_validator('permissions')
    @classmethod
    def grants(cls,value):return ManagedUserCreate.grants(value) if value is not None else value
    @field_validator('password')
    @classmethod
    def password_length(cls,value):return valid_password(value) if value is not None else value

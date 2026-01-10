import json
import os
import base64
from typing import Optional, cast
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta, timezone

from ..models.auth.user_response import UserResponse
from ..models.auth.user_token_data import TokenData
from ..models.auth.user_token import Token
from ..models.auth.user import User
from ..models.auth.hashed_password_response import HashedPasswordResponse

# Security Config
SECRET_KEY = cast(str, os.getenv("API_SECRET_KEY"))
if not SECRET_KEY:
    raise ValueError("API_SECRET_KEY environment variable is not set")
ALGORITHM = cast(str, os.getenv("API_AUTH_ALGORITHM"))
if not ALGORITHM:
    raise ValueError("API_AUTH_ALGORITHM environment variable is not set")
TOKEN_EXPIRES = int(cast(str, os.getenv("API_TOKEN_EXPIRES_MINUTES", "30")))

_ALLOWED_USERS = os.getenv("API_USERS")
if not _ALLOWED_USERS:
    raise ValueError("API_ALLOWED_USERS environment variable is not set")
ALLOWED_USERS_DB = json.loads(base64.b64decode(_ALLOWED_USERS).decode("utf-8"))["users"]

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# region Security Functions
def verify_pwd(plain_pwd: str, hashed_pwd: str) -> bool:
    return pwd_context.verify(plain_pwd, hashed_pwd)


def get_pwd_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRES)

    to_encode["exp"] = expire
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not verify credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return TokenData(username=username)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not verify credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# endregion Security Functions


# region Auth Dependencies


def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    token_data = verify_token(token)
    if token_data.username not in ALLOWED_USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = User(**ALLOWED_USERS_DB[token_data.username])
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=404,
            detail="Inactive User",
        )
    return current_user


# endregion Auth Dependencies


# region Auth Endpoints
@router.get(
    "/api/v1/auth/password_hash/{password}",
    response_model=HashedPasswordResponse,
)
async def get_hashed_password(
    password: str, current_user: User = Depends(get_current_active_user)
):
    """Generate a hashed password from a plain text password.

    This endpoint is primarily for development and testing purposes.
    In production, passwords should be hashed securely and not exposed via an API.

    - **password**: The plain text password to be hashed.

    Returns a JSON response containing the hashed password.
    """
    try:
        hashed_password = get_pwd_hash(password)
        print("Generated hashed password:", hashed_password)
        return HashedPasswordResponse(hashed_password=hashed_password)
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating hashed password: {str(e)}",
        )


@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user_dict = ALLOWED_USERS_DB.get(form_data.username)
    if not user_dict:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = User(**user_dict)
    if not verify_pwd(form_data.password, user.hashed_pwd):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=TOKEN_EXPIRES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@router.get("/profile", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.get("/api/v1/verify-token")
def verify_token_endpoint(current_user: User = Depends(get_current_active_user)):
    return {
        "valid": True,
        "user": {
            "username": current_user.username,
            "name": current_user.name,
            "email": current_user.email,
            "roles": current_user.roles,
        },
    }


# endregion Auth Endpoints

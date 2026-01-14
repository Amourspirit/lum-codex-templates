from typing import Optional
from fastapi import APIRouter, Security, HTTPException, Depends, status, Request
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    APIKeyHeader,
)
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta, timezone

from ..models.auth.hashed_password_response import HashedPasswordResponse
from ..models.auth.user import User
from ..models.auth.user_response import UserResponse
from ..models.auth.user_token import Token
from ..models.auth.user_token_data import TokenData
from ..models.auth.verify_token_response import VerifyTokenResponse
from ..routes.limiter import limiter
from ..lib.env import env_info


# API key via header
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

# print("Env Data:", API_ENV_DB)
router = APIRouter()


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token", auto_error=False)


# print("Loaded users:", _get_db_users())


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
        expire = datetime.now(timezone.utc) + timedelta(minutes=env_info.TOKEN_EXPIRES)

    to_encode["exp"] = expire
    encoded_jwt = jwt.encode(
        to_encode, env_info.SECRET_KEY, algorithm=env_info.ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(
            token, env_info.SECRET_KEY, algorithms=[env_info.ALGORITHM]
        )
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


def get_user(username: str) -> User:
    user = env_info.get_user_info(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


def get_current_principal(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    api_key: str | None = Security(api_key_header),
):
    # print("Authenticating request...")
    # If API key present and valid, accept it
    if api_key:
        valid_api_keys = env_info.get_hashed_api_keys()

        # print("Valid API keys:", valid_api_keys)
        for k in valid_api_keys:
            if verify_pwd(api_key, k):
                origin = request.headers.get("origin") or request.headers.get("referer")
                allowed_origins = env_info.get_api_key_allowed_origins(k)
                print("Request origin:", origin)
                if not origin or not any(origin.startswith(o) for o in allowed_origins):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Invalid origin",
                    )
                return {"type": "api_key", "key": api_key}
        # print("Invalid API key provided")

    # Otherwise fall back to OAuth2 token auth
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token_data = verify_token(token)
    if token_data.username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token. Missing username",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = get_user(token_data.username)

    return {"type": "oauth2", "sub": user.username}


def get_current_active_principle(
    current_principle: dict[str, str] = Depends(get_current_principal),
) -> dict[str, str]:
    # print("Current principle:", current_principle)
    if current_principle["type"] == "api_key":
        # For API key auth, we don't have a user context
        return {"type": "api_key", "key": current_principle["key"]}

    current_user = get_user(current_principle["sub"])
    if not current_user.is_active:
        raise HTTPException(
            status_code=404,
            detail="Inactive User",
        )
    return {"type": "oauth2", "sub": current_user.username}


# endregion Auth Dependencies


# region Auth Endpoints
@router.get(
    "/api/v1/auth/password_hash/{password}",
    response_model=HashedPasswordResponse,
)
@limiter.limit("15/minute")
async def get_hashed_password(
    password: str,
    request: Request,
    current_principle: dict[str, str] = Depends(get_current_active_principle),
):
    """Generate a hashed password from a plain text password.

    This endpoint is primarily for development and testing purposes.
    In production, passwords should be hashed securely and not exposed via an API.

    - **password**: The plain text password to be hashed.

    Returns a JSON response containing the hashed password.
    """
    try:
        hashed_password = get_pwd_hash(password)
        # print("Generated hashed password:", hashed_password)
        return HashedPasswordResponse(hashed_password=hashed_password)
    except Exception as e:
        # print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating hashed password: {str(e)}",
        )


@router.post("/api/v1/token", response_model=Token)
@limiter.limit("5/minute")
def login_for_access_token(
    request: Request, form_data: OAuth2PasswordRequestForm = Depends()
):
    user = env_info.get_user_info(form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # user = User(**user_dict)
    if not verify_pwd(form_data.password, user.hashed_pwd):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=env_info.TOKEN_EXPIRES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@router.get("/api/v1/profile", response_model=UserResponse)
@limiter.limit("15/minute")
def get_profile(
    request: Request,
    current_principle: dict[str, str] = Depends(get_current_active_principle),
):
    if current_principle["type"] == "api_key":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key authentication does not have a user profile",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = get_user(current_principle["sub"])
    return UserResponse(
        username=user.username,
        name=user.name,
        email=user.email,
        roles=user.roles,
        is_active=user.is_active,
        monad_name=user.monad_name,
    )


@router.get("/api/v1/verify-token", response_model=VerifyTokenResponse)
@limiter.limit("15/minute")
def verify_token_endpoint(
    request: Request,
    current_principle: dict[str, str] = Depends(get_current_active_principle),
):
    if current_principle["type"] == "api_key":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key authentication does not have a user profile",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = get_user(current_principle["sub"])
    return VerifyTokenResponse(
        valid=True,
        username=user.username,
        name=user.name,
        email=user.email,
        roles=user.roles,
    )


# endregion Auth Endpoints

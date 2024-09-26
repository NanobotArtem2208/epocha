import hashlib
import secrets
from datetime import datetime, timezone, timedelta

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
  
)  
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_async_session
from fastapi.security import OAuth2PasswordRequestForm
from config.config import settings

from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/auth", tags=["auth"])

def generate_token(): 
    return secrets.token_urlsafe(32)

def generate_expiry_date():
    expire_date = datetime.now(timezone.utc) + timedelta(days=1)
    return expire_date.isoformat()

@router.post("/login")
async def login(
    data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_async_session),
):

    login = data.username
    password = data.password

    if not login or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Login and password are required",
        )

    settings_login = settings.LOGIN.get_secret_value()
    settings_password = settings.PASSWORD.get_secret_value()

    password_hash = hashlib.sha256(password.encode()).hexdigest()
    settings_password_hash = hashlib.sha256(settings_password.encode()).hexdigest()

    if login == settings_login and password_hash == settings_password_hash:
        token = generate_token()

        resp = RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)
        resp.set_cookie(
            key="auth_token",
            value=token,
            expires=generate_expiry_date(),
            httponly=True,
            secure=False,
        )
        return resp

    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid login or password"
        )

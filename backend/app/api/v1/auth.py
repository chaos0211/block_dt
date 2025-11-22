# app/api/v1/auth.py
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4

from app.core.config import settings
from app.core.security import verify_password, create_access_token
from app.db.base import get_session as get_db
from app.db.models.user import User
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserResponse
from app.core.security import get_password_hash

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    # 这里用 username 字段，也可以改成 email 登录
    result = await db.execute(
        select(User).where(User.username == form_data.username)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password",
        )

    if not verify_password(form_data.password, user.hash_passwd):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password",
        )

    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    access_token = create_access_token(
        data={"sub": str(user.id)},  # token 里只放 user_id 即可
        expires_delta=access_token_expires,
    )
    return Token(access_token=access_token)

@router.post("/register", response_model=UserResponse)
async def create_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    # 检查用户名 / 邮箱是否已存在
    result = await db.execute(
        select(User).where(User.username == user_in.username)
    )
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    result = await db.execute(
        select(User).where(User.email == user_in.email)
    )
    existing_email_user = result.scalars().first()
    if existing_email_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # bcrypt 限制明文密码不能超过 72 字节
    try:
        if len(user_in.password.encode("utf-8")) > 72:
            raise HTTPException(
                status_code=400,
                detail="密码过长，请控制在 72 字节以内（建议不超过 20–24 个字符的中英文组合）",
            )
        hashed_pwd = get_password_hash(user_in.password)
    except ValueError:
        # 兜底：如果底层仍然因为长度问题抛错，转换为 HTTP 错误返回
        raise HTTPException(
            status_code=400,
            detail="密码过长，请控制在 72 字节以内（建议不超过 20–24 个字符的中英文组合）",
        )

    wallet_address = "0x" + uuid4().hex

    db_user = User(
        username=user_in.username,
        email=user_in.email,
        wallet_address=wallet_address,
        is_admin=user_in.is_admin,
        hash_passwd=hashed_pwd,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user
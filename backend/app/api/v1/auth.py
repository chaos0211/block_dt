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

from typing import List, Optional

from pydantic import BaseModel, EmailStr

from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    wallet_address: Optional[str] = None
    balance: Optional[float] = None
    is_admin: Optional[bool] = None
    password: Optional[str] = None


# 普通用户自身信息更新 schema
class MeUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


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


# 获取当前登录用户信息（所有登录用户可用）

@router.get("/me", response_model=UserResponse)
async def me(
    current_user: User = Depends(get_current_user),
):
    """获取当前登录用户信息（所有登录用户可用）"""
    return current_user


# 普通用户更新自身信息（仅允许修改：username / email / password）
@router.put("/me", response_model=UserResponse)
async def update_me(
    me_in: MeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新当前登录用户信息（仅允许修改：username / email / password）"""

    # 重新从库里取当前用户，避免直接修改 Depends 注入对象带来的状态问题
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # username 唯一性校验
    if me_in.username is not None and me_in.username != user.username:
        chk = await db.execute(select(User).where(User.username == me_in.username))
        if chk.scalars().first():
            raise HTTPException(status_code=400, detail="Username already registered")
        user.username = me_in.username

    # email 唯一性校验
    if me_in.email is not None and me_in.email != user.email:
        chk = await db.execute(select(User).where(User.email == me_in.email))
        if chk.scalars().first():
            raise HTTPException(status_code=400, detail="Email already registered")
        user.email = me_in.email

    # password 更新（同注册规则：bcrypt 明文 <= 72 bytes）
    if me_in.password:
        try:
            if len(me_in.password.encode("utf-8")) > 72:
                raise HTTPException(
                    status_code=400,
                    detail="密码过长，请控制在 72 字节以内（建议不超过 20–24 个字符的中英文组合）",
                )
            user.hash_passwd = get_password_hash(me_in.password)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="密码过长，请控制在 72 字节以内（建议不超过 20–24 个字符的中英文组合）",
            )

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

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


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    page: int = 1,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    用户列表（仅管理员可见）
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    if page < 1:
        page = 1
    if limit < 1:
        limit = 10

    offset = (page - 1) * limit
    result = await db.execute(
        select(User).offset(offset).limit(limit)
    )
    users = result.scalars().all()
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取单个用户详情（仅管理员可见）
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    更新用户信息（仅管理员可操作）
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # 可选字段更新
    if user_in.username is not None:
        user.username = user_in.username
    if user_in.email is not None:
        user.email = user_in.email
    if user_in.is_admin is not None:
        user.is_admin = user_in.is_admin
    if user_in.wallet_address is not None:
        user.wallet_address = user_in.wallet_address
    if user_in.balance is not None:
        user.balance = user_in.balance

    # 如果需要更新密码，按注册时同样的规则限制长度并重新哈希
    if user_in.password:
        try:
            if len(user_in.password.encode("utf-8")) > 72:
                raise HTTPException(
                    status_code=400,
                    detail="密码过长，请控制在 72 字节以内（建议不超过 20–24 个字符的中英文组合）",
                )
            user.hash_passwd = get_password_hash(user_in.password)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="密码过长，请控制在 72 字节以内（建议不超过 20–24 个字符的中英文组合）",
            )

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    删除用户（仅管理员可操作）
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    await db.delete(user)
    await db.commit()
    # 204 No Content 不需要返回体
    return None
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Numeric
from sqlalchemy.sql import func
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hash_passwd = Column(String(255), nullable=False)

    # 区块链钱包地址
    wallet_address = Column(String(64), unique=True, index=True, nullable=False)

    # 状态 & 权限
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    # 账户余额（链上/链下记账，看你后面如何设计）
    balance = Column(Numeric(18, 8), default=0)

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
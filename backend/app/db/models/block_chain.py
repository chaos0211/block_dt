from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean
from sqlalchemy.sql import func
from app.db.base import Base


class Block(Base):
    __tablename__ = "blocks"

    id = Column(Integer, primary_key=True, index=True)
    block_number = Column(Integer, unique=True, nullable=False)
    block_hash = Column(String(64), unique=True, nullable=False)
    previous_hash = Column(String(64), nullable=False)
    merkle_root = Column(String(64), nullable=False)
    nonce = Column(Integer, nullable=False)
    difficulty = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    miner_address = Column(String(64), nullable=False)
    reward = Column(Float, default=0.0)
    transaction_count = Column(Integer, default=0)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_hash = Column(String(64), unique=True, nullable=False)
    from_address = Column(String(64), nullable=False)
    to_address = Column(String(64), nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String(64), nullable=False)  # donation, project_creation, reward
    block_hash = Column(String(64), nullable=True)
    block_number = Column(Integer, nullable=True)
    gas_fee = Column(Float, default=0.0)
    data = Column(Text, nullable=True)  # JSON格式的额外数据
    is_confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    confirmed_at = Column(DateTime(timezone=True), nullable=True)


class TransactionPool(Base):
    __tablename__ = "transaction_pool"

    id = Column(Integer, primary_key=True, index=True)
    transaction_hash = Column(String(64), unique=True, nullable=False)
    from_address = Column(String(64), nullable=False)
    to_address = Column(String(64), nullable=False)
    amount = Column(Float, nullable=False)
    gas_fee = Column(Float, nullable=False)
    data = Column(Text, nullable=True)
    priority_score = Column(Float, nullable=False)  # 基于gas费用的优先级分数
    created_at = Column(DateTime(timezone=True), server_default=func.now())
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from app.db.base import Base


class TransactionStatus(str, Enum):
    PENDING = "pending"
    IN_POOL = "in_pool"
    MINING = "mining"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class Donation(Base):
    __tablename__ = "donations"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    donor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    status = Column(String(64), default=TransactionStatus.PENDING.value)
    transaction_hash = Column(String(64), unique=True, nullable=True)
    block_hash = Column(String(64), nullable=True)
    block_number = Column(Integer, nullable=True)
    gas_fee = Column(Float, default=0.0)
    is_anonymous = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    confirmed_at = Column(DateTime(timezone=True), nullable=True)

    donor = relationship("User", backref="donations")
    project = relationship("Project", backref="donations")
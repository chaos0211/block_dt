from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from app.db.base import Base


class ProjectStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ON_CHAIN = "on_chain"
    COMPLETED = "completed"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(64), nullable=False, index=True)
    description = Column(Text, nullable=False)
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(64), default=ProjectStatus.PENDING.value)
    blockchain_address = Column(String(64), unique=True, nullable=True)
    blockchain_tx_hash = Column(String(64), unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)
    on_chain_at = Column(DateTime(timezone=True), nullable=True)

    creator = relationship("User", backref="created_projects")
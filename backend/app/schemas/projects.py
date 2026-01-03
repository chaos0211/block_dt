from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from app.db.models.projects import ProjectStatus


class ProjectBase(BaseModel):
    title: str
    description: str
    target_amount: float
    img_url: Optional[str] = None

    @validator('target_amount')
    def validate_target_amount(cls, v):
        if v <= 0:
            raise ValueError('目标金额必须大于0')
        return v


class ProjectCreate(ProjectBase):
    pass


class ProjectApprove(BaseModel):
    approved: bool
    rejection_reason: Optional[str] = None
    approved_at: Optional[datetime] = None


class ProjectResponse(ProjectBase):
    id: int
    current_amount: float
    # img_url: Optional[str] = None
    creator_id: int
    status: ProjectStatus
    blockchain_address: Optional[str] = None
    blockchain_tx_hash: Optional[str] = None
    created_at: datetime
    approved_at: Optional[datetime] = None
    on_chain_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class ProjectList(BaseModel):
    projects: List[ProjectResponse]
    total: int
    page: int
    size: int
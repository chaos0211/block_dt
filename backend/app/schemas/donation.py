from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
from app.db.models.donation import TransactionStatus


class DonationBase(BaseModel):
    amount: float
    project_id: int
    is_anonymous: bool = False

    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('捐赠金额必须大于0')
        return v


class DonationCreate(DonationBase):
    pass


class DonationResponse(DonationBase):
    id: int
    donor_id: int
    status: TransactionStatus
    transaction_hash: Optional[str] = None
    block_hash: Optional[str] = None
    block_number: Optional[int] = None
    gas_fee: float
    created_at: datetime
    confirmed_at: Optional[datetime] = None

    class Config:
        orm_mode = True
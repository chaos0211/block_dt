from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.base import get_session as get_db
from app.schemas.donation import DonationCreate, DonationResponse
from app.services.donation import DonationService

router = APIRouter(prefix="/api/v1/donations", tags=["auth"])



@router.post("/", response_model=DonationResponse, status_code=status.HTTP_201_CREATED)
async def create_donation(
        donation_data: DonationCreate,
        donor_id: int,  # 实际应用中从JWT token获取
        db: Session = Depends(get_db)
):
    """创建捐赠交易"""
    service = DonationService(db)
    donation = service.create_donation(donation_data, donor_id)

    if not donation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="捐赠创建失败，请检查项目状态和账户余额"
        )

    return donation


@router.get("/{donation_id}", response_model=DonationResponse)
async def get_donation(
        donation_id: int,
        db: Session = Depends(get_db)
):
    """获取捐赠详情"""
    service = DonationService(db)
    donation = service.get_donation(donation_id)

    if not donation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="捐赠记录不存在"
        )

    return donation


@router.get("/user/{user_id}")
async def get_user_donations(
        user_id: int,
        page: int = 1,
        size: int = 10,
        db: Session = Depends(get_db)
):
    """获取用户的捐赠记录"""
    service = DonationService(db)
    donations, total = service.get_user_donations(user_id, page, size)

    return {
        "donations": donations,
        "total": total,
        "page": page,
        "size": size
    }


@router.get("/project/{project_id}")
async def get_project_donations(
        project_id: int,
        page: int = 1,
        size: int = 10,
        db: Session = Depends(get_db)
):
    """获取项目的捐赠记录"""
    service = DonationService(db)
    donations, total = service.get_project_donations(project_id, page, size)

    return {
        "donations": donations,
        "total": total,
        "page": page,
        "size": size
    }


@router.get("/statistics")
async def get_donation_statistics(
        project_id: Optional[int] = None,
        db: Session = Depends(get_db)
):
    """获取捐赠统计信息"""
    service = DonationService(db)
    statistics = service.get_donation_statistics(project_id)

    return statistics
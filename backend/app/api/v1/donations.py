from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.db.base import get_session as get_db
from app.schemas.donation import DonationCreate, DonationResponse
from app.services.donation import DonationService
from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.models.donation import Donation
from app.db.models.projects import Project

router = APIRouter(prefix="/api/v1/donations", tags=["donations"])



@router.post("/", response_model=DonationResponse, status_code=status.HTTP_201_CREATED)
async def create_donation(
        donation_data: DonationCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    """创建捐赠交易"""
    service = DonationService(db)
    donation = await service.create_donation(donation_data, current_user.id)
    if not donation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="捐赠创建失败，请检查项目状态和账户余额"
        )

    return donation


@router.get("/")
async def list_latest_donations(
        page: int = 1,
        limit: int = 5,
        db: AsyncSession = Depends(get_db),
):
    """
    获取最新的捐赠记录（按时间倒序）
    - 默认返回最近 5 条
    - 支持通过 page / limit 进行简单分页
    - 额外返回项目名称(project_name)和捐赠人名称(donor_name)
    """
    if page < 1:
        page = 1
    if limit < 1:
        limit = 5

    offset = (page - 1) * limit

    # 联表查询 Donation / Project / User，拿到项目名称和用户名
    stmt = (
        select(Donation, Project.title, User.username)
        .join(Project, Donation.project_id == Project.id)
        .join(User, Donation.donor_id == User.id)
        .order_by(Donation.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    result = await db.execute(stmt)
    rows = result.all()

    donations_with_names = []
    for donation, project_title, username in rows:
        donations_with_names.append({
            "id": donation.id,
            "amount": donation.amount,
            "donor_id": donation.donor_id,
            "project_id": donation.project_id,
            "status": donation.status,
            "transaction_hash": donation.transaction_hash,
            "block_hash": donation.block_hash,
            "block_number": donation.block_number,
            "gas_fee": donation.gas_fee,
            "is_anonymous": donation.is_anonymous,
            "created_at": donation.created_at,
            "confirmed_at": donation.confirmed_at,
            # 新增字段：项目名称和捐赠人名称
            "project_name": project_title,
            "donor_name": username,
        })

    return donations_with_names


@router.get("/{donation_id}", response_model=DonationResponse)
async def get_donation(
        donation_id: int,
        db: AsyncSession = Depends(get_db)
):
    """获取捐赠详情"""
    service = DonationService(db)
    donation = await service.get_donation(donation_id)

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
        db: AsyncSession = Depends(get_db)
):
    """获取用户的捐赠记录"""
    service = DonationService(db)
    donations, total = await service.get_user_donations(user_id, page, size)

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
        db: AsyncSession = Depends(get_db)
):
    """获取项目的捐赠记录"""
    service = DonationService(db)
    donations, total = await service.get_project_donations(project_id, page, size)

    return {
        "donations": donations,
        "total": total,
        "page": page,
        "size": size
    }


@router.get("/statistics")
async def get_donation_statistics(
        project_id: Optional[int] = None,
        db: AsyncSession = Depends(get_db)
):
    """获取捐赠统计信息"""
    service = DonationService(db)
    statistics = await service.get_donation_statistics(project_id)

    return statistics
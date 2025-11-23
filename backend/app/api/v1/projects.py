from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.base import get_session as get_db
from app.schemas.projects import (
    ProjectCreate,
    ProjectApprove,
    ProjectResponse,
    ProjectList,
)
from app.db.models.projects import Project, ProjectStatus

# 服务层导入
from app.services.projects import ProjectService
from app.api.deps import get_current_user
from app.db.models.user import User

router = APIRouter(prefix="/api/v1/projects", tags=["auth"])


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建新的爱心项目"""
    project = Project(
        title=project_data.title,
        description=project_data.description,
        target_amount=project_data.target_amount,
        current_amount=0.0,
        creator_id=current_user.id,
        status=ProjectStatus.PENDING.value,
    )

    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.put("/{project_id}/approve", response_model=ProjectResponse)
async def approve_project(
    project_id: int,
    approval_data: ProjectApprove,
    db: AsyncSession = Depends(get_db),
):
    """审核项目（调用服务层逻辑）"""
    service = ProjectService(db)
    project = await service.approve_project(project_id, approval_data)

    if not project:
        # 进一步区分：项目不存在 vs 状态不允许审核
        result = await db.execute(select(Project).where(Project.id == project_id))
        exists = result.scalars().first()
        if not exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="项目不存在",
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前状态不允许审核",
        )

    return project


@router.put("/{project_id}/on-chain", response_model=ProjectResponse)
async def put_project_on_chain(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """将已审核项目上链（调用服务层逻辑）"""
    service = ProjectService(db)
    project = await service.put_project_on_chain(project_id)

    if not project:
        # 同样区分：项目不存在 vs 状态不允许上链
        result = await db.execute(select(Project).where(Project.id == project_id))
        exists = result.scalars().first()
        if not exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="项目不存在",
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前状态不允许上链",
        )

    return project


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取项目详情"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project: Optional[Project] = result.scalars().first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )

    return project


@router.get("/", response_model=ProjectList)
async def get_projects(
    status: Optional[str] = None,
    page: int = 1,
    size: int = Query(10, alias="limit"),
    db: AsyncSession = Depends(get_db),
):
    """获取项目列表"""

    stmt = select(Project)
    if status:
        stmt = stmt.where(Project.status == status.upper())

    # 总数
    result_all = await db.execute(stmt)
    all_projects = result_all.scalars().all()
    total = len(all_projects)

    # 分页
    stmt_page = (
        stmt.order_by(Project.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    result_page = await db.execute(stmt_page)
    projects = result_page.scalars().all()

    # 将 ORM 对象转换为 Pydantic 模型，兼容 Pydantic v2
    project_items = [
        ProjectResponse.model_validate(p, from_attributes=True)
        for p in projects
    ]

    return ProjectList(
        projects=project_items,
        total=total,
        page=page,
        size=size,
    )


@router.get("/{project_id}/progress")
async def get_project_progress(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取项目进度"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project: Optional[Project] = result.scalars().first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )

    target = project.target_amount or 0.0
    current = project.current_amount or 0.0
    progress = 0.0
    if target > 0:
        progress = float(current) / float(target)

    return {
        "project_id": project.id,
        "title": project.title,
        "target_amount": project.target_amount,
        "current_amount": project.current_amount,
        "progress": progress,
    }
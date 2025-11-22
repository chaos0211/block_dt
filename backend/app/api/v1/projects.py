from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.base import get_session as get_db
from app.schemas.projects import ProjectCreate, ProjectApprove, ProjectResponse, ProjectList
from app.services.projects import ProjectService
from app.db.models.projects import ProjectStatus

router = APIRouter(prefix="/api/v1/projects", tags=["auth"])



@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
        project_data: ProjectCreate,
        creator_id: int,  # 实际应用中从JWT token获取
        db: Session = Depends(get_db)
):
    """创建新的爱心项目"""
    service = ProjectService(db)
    project = service.create_project(project_data, creator_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="项目创建失败"
        )

    return project


@router.put("/{project_id}/approve", response_model=ProjectResponse)
async def approve_project(
        project_id: int,
        approval_data: ProjectApprove,
        db: Session = Depends(get_db)
):
    """审核项目"""
    service = ProjectService(db)
    project = service.approve_project(project_id, approval_data)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在或状态无效"
        )

    return project


@router.put("/{project_id}/on-chain", response_model=ProjectResponse)
async def put_project_on_chain(
        project_id: int,
        db: Session = Depends(get_db)
):
    """将已审核项目上链"""
    service = ProjectService(db)
    project = service.put_project_on_chain(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="项目上链失败，请检查项目状态"
        )

    return project


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
        project_id: int,
        db: Session = Depends(get_db)
):
    """获取项目详情"""
    service = ProjectService(db)
    project = service.get_project(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )

    return project


@router.get("/", response_model=ProjectList)
async def get_projects(
        status: ProjectStatus = None,
        page: int = 1,
        size: int = 10,
        db: Session = Depends(get_db)
):
    """获取项目列表"""
    service = ProjectService(db)
    projects, total = service.get_projects(status, page, size)

    return ProjectList(
        projects=projects,
        total=total,
        page=page,
        size=size
    )


@router.get("/{project_id}/progress")
async def get_project_progress(
        project_id: int,
        db: Session = Depends(get_db)
):
    """获取项目进度"""
    service = ProjectService(db)
    progress = service.get_project_progress(project_id)

    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )

    return progress
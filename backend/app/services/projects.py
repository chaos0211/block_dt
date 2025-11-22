from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models.projects import Project, ProjectStatus
from app.db.models.user import User
from app.schemas.projects import ProjectCreate, ProjectApprove
from app.services.block_chain import ProjectBlockchainService, BlockchainService
import datetime


class ProjectService:
    def __init__(self, db: Session):
        self.db = db
        self.blockchain_service = ProjectBlockchainService(
            db, BlockchainService(db)
        )

    def create_project(self, project_data: ProjectCreate, creator_id: int) -> Optional[Project]:
        """创建新项目"""
        try:
            project = Project(
                title=project_data.title,
                description=project_data.description,
                target_amount=project_data.target_amount,
                creator_id=creator_id,
                status=ProjectStatus.PENDING
            )

            self.db.add(project)
            self.db.commit()
            self.db.refresh(project)

            return project
        except Exception as e:
            self.db.rollback()
            return None

    def approve_project(self, project_id: int, approval_data: ProjectApprove) -> Optional[Project]:
        """审核项目"""
        project = self.db.query(Project).filter(Project.id == project_id).first()

        if not project:
            return None

        if project.status != ProjectStatus.PENDING:
            return None

        if approval_data.approved:
            project.status = ProjectStatus.APPROVED
            project.approved_at = datetime.datetime.utcnow()
        else:
            project.status = ProjectStatus.REJECTED

        try:
            self.db.commit()
            self.db.refresh(project)
            return project
        except Exception as e:
            self.db.rollback()
            return None

    def put_project_on_chain(self, project_id: int) -> Optional[Project]:
        """将已审核项目上链"""
        project = self.db.query(Project).filter(Project.id == project_id).first()

        if not project:
            return None

        if project.status != ProjectStatus.APPROVED:
            return None

        # 创建区块链地址并上链
        blockchain_address = self.blockchain_service.put_project_on_chain(
            project.id, project.title, project.target_amount
        )

        if blockchain_address:
            project.blockchain_address = blockchain_address
            project.status = ProjectStatus.ON_CHAIN
            project.on_chain_at = datetime.datetime.utcnow()

            try:
                self.db.commit()
                self.db.refresh(project)
                return project
            except Exception as e:
                self.db.rollback()
                return None

        return None

    def get_project(self, project_id: int) -> Optional[Project]:
        """获取单个项目"""
        return self.db.query(Project).filter(Project.id == project_id).first()

    def get_projects(self, status: Optional[ProjectStatus] = None,
                     page: int = 1, size: int = 10) -> tuple[List[Project], int]:
        """获取项目列表"""
        query = self.db.query(Project)

        if status:
            query = query.filter(Project.status == status)

        total = query.count()
        projects = (
            query.order_by(Project.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )

        return projects, total

    def get_project_progress(self, project_id: int) -> Optional[dict]:
        """获取项目进度"""
        project = self.get_project(project_id)
        if not project:
            return None

        progress_percentage = (
            (project.current_amount / project.target_amount) * 100
            if project.target_amount > 0 else 0
        )

        donation_count = len(project.donations)

        return {
            "project_id": project.id,
            "current_amount": project.current_amount,
            "target_amount": project.target_amount,
            "progress_percentage": round(progress_percentage, 2),
            "donation_count": donation_count,
            "status": project.status
        }
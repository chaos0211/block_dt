from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.models.projects import Project, ProjectStatus
from app.db.models.user import User
from app.schemas.projects import ProjectCreate, ProjectApprove
from app.services.block_chain import ProjectBlockchainService, BlockchainService
import datetime


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.blockchain_service = ProjectBlockchainService(
            db, BlockchainService(db)
        )

    async def create_project(self, project_data: ProjectCreate, creator_id: int) -> Optional[Project]:
        """创建新项目（使用 AsyncSession）"""
        try:
            project = Project(
                title=project_data.title,
                description=project_data.description,
                target_amount=project_data.target_amount,
                creator_id=creator_id,
                status=ProjectStatus.PENDING.value,
            )

            self.db.add(project)
            await self.db.commit()
            await self.db.refresh(project)

            return project
        except Exception:
            await self.db.rollback()
            return None

    async def approve_project(self, project_id: int, approval_data: ProjectApprove) -> Optional[Project]:
        """审核项目：仅允许对 PENDING 状态项目进行通过或拒绝"""
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        project = result.scalars().first()

        if not project:
            return None

        # 仅在待审核状态下允许审核
        if project.status != ProjectStatus.PENDING.value:
            return None

        if approval_data.approved:
            project.status = ProjectStatus.APPROVED.value
            project.approved_at = datetime.datetime.utcnow()
        else:
            project.status = ProjectStatus.REJECTED.value
            # 拒绝时可以根据需要记录原因（若模型中有对应字段可在此处赋值）

        try:
            await self.db.commit()
            await self.db.refresh(project)
            return project
        except Exception:
            await self.db.rollback()
            return None

    async def put_project_on_chain(self, project_id: int) -> Optional[Project]:
        """将已审核项目上链：仅在 APPROVED 状态下允许，成功后状态改为 ON_CHAIN"""
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        project = result.scalars().first()

        if not project:
            return None

        # 仅允许对已审核通过的项目执行上链
        if project.status != ProjectStatus.APPROVED.value:
            return None

        # 创建区块链地址并上链：由区块链服务负责具体链上记录/挖矿等逻辑
        try:
            blockchain_address = self.blockchain_service.put_project_on_chain(
                project.id,
                project.title,
                project.target_amount,
            )
        except Exception:
            # 区块链服务异常，视为上链失败
            return None

        if not blockchain_address:
            # 未返回有效地址，同样视为上链失败
            return None

        project.blockchain_address = blockchain_address
        project.status = ProjectStatus.ON_CHAIN.value
        project.on_chain_at = datetime.datetime.utcnow()

        try:
            await self.db.commit()
            await self.db.refresh(project)
            return project
        except Exception:
            await self.db.rollback()
            return None

    async def get_project(self, project_id: int) -> Optional[Project]:
        """获取单个项目"""
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        return result.scalars().first()

    async def get_projects(self, status: Optional[ProjectStatus] = None,
                     page: int = 1, size: int = 10) -> tuple[List[Project], int]:
        """获取项目列表"""
        stmt = select(Project)

        if status:
            stmt = stmt.where(Project.status == status)

        result = await self.db.execute(stmt)
        items = result.scalars()

        total = len(items)

        # pagination
        stmt = (
            stmt.order_by(Project.created_at.desc())
                .offset((page - 1) * size)
                .limit(size)
        )

        result = await self.db.execute(stmt)
        projects = result.scalars().all()

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
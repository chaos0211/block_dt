from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.models.projects import Project, ProjectStatus
from app.db.models.user import User
from app.schemas.projects import ProjectCreate, ProjectApprove
from app.services.block_chain import ProjectBlockchainService, BlockchainService
import datetime
from app.db.models.block_chain import TransactionPool
import json


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
        """将已审核项目提交上链：仅在 APPROVED 状态下允许，将创世交易加入交易池。

        注意：此处仅负责构造并提交 project_creation 交易到交易池，
        真正的区块打包与状态更新（ON_CHAIN）应在挖矿逻辑完成后进行。
        """
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        project = result.scalars().first()

        if not project:
            return None

        # 仅允许对已审核通过的项目执行上链请求（大小写兼容）
        status_value = (project.status or "").lower()
        if status_value != ProjectStatus.APPROVED.value.lower():
            return None

        # 防止重复提交：若该项目已存在未打包的 project_creation 交易，则直接返回项目
        existing_stmt = select(TransactionPool).where(TransactionPool.data.isnot(None))
        existing_result = await self.db.execute(existing_stmt)
        for pool_tx in existing_result.scalars().all():
            try:
                data = json.loads(pool_tx.data) if pool_tx.data else {}
            except Exception:
                data = {}
            if not isinstance(data, dict):
                continue
            if data.get("tx_type") == "project_creation" and data.get("project_id") == project.id:
                # 已在交易池中，无需再次创建
                return project

        try:
            # 调用区块链服务：生成项目地址（如有需要）并构造 project_creation 交易写入交易池
            blockchain_address = self.blockchain_service.put_project_on_chain(
                project.id,
                project.title,
                project.target_amount,
            )
        except Exception:
            # 区块链服务异常，视为上链请求失败
            return None

        if not blockchain_address:
            # 未返回有效地址，同样视为上链请求失败
            return None

        # 仅更新项目的链上地址，不在此处修改状态和 on_chain_at，
        # 避免在未真正打包进区块前就认为已上链
        project.blockchain_address = blockchain_address

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

        total_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar_one()

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
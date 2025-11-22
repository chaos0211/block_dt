from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models.donation import Donation, TransactionStatus
from ..models.project import Project
from ..models.user import User
from ..schemas.donation import DonationCreate
from .blockchain_service import BlockchainService, TransactionData
import time
import uuid


class DonationService:
    def __init__(self, db: Session):
        self.db = db
        self.blockchain = BlockchainService(db)

    def create_donation(self, donation_data: DonationCreate, donor_id: int) -> Optional[Donation]:
        """创建捐赠交易"""
        # 验证项目是否存在且已上链
        project = self.db.query(Project).filter(
            Project.id == donation_data.project_id,
            Project.status == "on_chain"
        ).first()

        if not project:
            return None

        # 验证用户余额
        donor = self.db.query(User).filter(User.id == donor_id).first()
        if not donor or donor.balance < donation_data.amount:
            return None

        try:
            # 创建捐赠记录
            donation = Donation(
                amount=donation_data.amount,
                donor_id=donor_id,
                project_id=donation_data.project_id,
                status=TransactionStatus.PENDING,
                is_anonymous=donation_data.is_anonymous,
                gas_fee=0.01  # 固定gas费用
            )

            self.db.add(donation)
            self.db.commit()
            self.db.refresh(donation)

            # 生成交易哈希
            timestamp = str(int(time.time()))
            transaction_hash = self.blockchain.generate_transaction_hash(
                donor.wallet_address,
                project.blockchain_address,
                donation_data.amount,
                timestamp
            )

            donation.transaction_hash = transaction_hash

            # 创建交易数据
            transaction_data = TransactionData(
                transaction_hash=transaction_hash,
                from_address=donor.wallet_address,
                to_address=project.blockchain_address,
                amount=donation_data.amount,
                transaction_type="donation",
                gas_fee=donation.gas_fee,
                data={
                    "donation_id": donation.id,
                    "project_id": project.id,
                    "donor_id": donor_id,
                    "is_anonymous": donation_data.is_anonymous,
                    "timestamp": timestamp
                }
            )

            # 添加到交易池
            if self.blockchain.add_transaction_to_pool(transaction_data):
                donation.status = TransactionStatus.IN_POOL

                # 暂时冻结用户资金
                donor.balance -= (donation_data.amount + donation.gas_fee)

                self.db.commit()
                self.db.refresh(donation)

                return donation
            else:
                # 添加到交易池失败，删除捐赠记录
                self.db.delete(donation)
                self.db.commit()
                return None

        except Exception as e:
            self.db.rollback()
            return None

    def get_donation(self, donation_id: int) -> Optional[Donation]:
        """获取单个捐赠记录"""
        return self.db.query(Donation).filter(Donation.id == donation_id).first()

    def get_user_donations(self, user_id: int, page: int = 1, size: int = 10) -> tuple[List[Donation], int]:
        """获取用户的捐赠记录"""
        query = self.db.query(Donation).filter(Donation.donor_id == user_id)

        total = query.count()
        donations = (
            query.order_by(Donation.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )

        return donations, total

    def get_project_donations(self, project_id: int, page: int = 1, size: int = 10) -> tuple[List[Donation], int]:
        """获取项目的捐赠记录"""
        query = self.db.query(Donation).filter(
            Donation.project_id == project_id,
            Donation.status == TransactionStatus.CONFIRMED
        )

        total = query.count()
        donations = (
            query.order_by(Donation.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )

        return donations, total

    def confirm_donation(self, transaction_hash: str, block_hash: str, block_number: int) -> bool:
        """确认捐赠交易"""
        donation = self.db.query(Donation).filter(
            Donation.transaction_hash == transaction_hash
        ).first()

        if not donation:
            return False

        try:
            # 更新捐赠状态
            donation.status = TransactionStatus.CONFIRMED
            donation.block_hash = block_hash
            donation.block_number = block_number
            donation.confirmed_at = func.now()

            # 更新项目筹款金额
            project = self.db.query(Project).filter(
                Project.id == donation.project_id
            ).first()

            if project:
                project.current_amount += donation.amount

            self.db.commit()
            return True

        except Exception as e:
            self.db.rollback()
            return False

    def get_donation_statistics(self, project_id: Optional[int] = None) -> dict:
        """获取捐赠统计信息"""
        query = self.db.query(Donation).filter(
            Donation.status == TransactionStatus.CONFIRMED
        )

        if project_id:
            query = query.filter(Donation.project_id == project_id)

        total_amount = query.with_entities(func.sum(Donation.amount)).scalar() or 0
        total_count = query.count()

        return {
            "total_amount": total_amount,
            "total_count": total_count,
            "average_amount": total_amount / total_count if total_count > 0 else 0
        }
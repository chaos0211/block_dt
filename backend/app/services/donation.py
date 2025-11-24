from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.models.donation import Donation, TransactionStatus
from app.db.models.projects import Project, ProjectStatus
from app.db.models.user import User
from app.schemas.donation import DonationCreate
from app.services.block_chain import BlockchainService, TransactionData
from decimal import Decimal
import time
from datetime import datetime, timedelta, timezone
CN_TZ = timezone(timedelta(hours=8))


class DonationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.blockchain = BlockchainService(db)

    async def create_donation(self, donation_data: DonationCreate, donor_id: int) -> Optional[Donation]:
        stmt = select(Project).where(
            Project.id == donation_data.project_id,
            Project.status == ProjectStatus.ON_CHAIN.value
        )
        result = await self.db.execute(stmt)
        project = result.scalars().first()
        print("DEBUG: project =", project)
        if not project:
            return None

        result = await self.db.execute(select(User).where(User.id == donor_id))
        donor = result.scalars().first()
        print("DEBUG: donor =", donor, "balance =", donor.balance if donor else None)
        if (not donor) or (donor.balance < donation_data.amount):
            print("DEBUG: insufficient balance or donor missing")
            return None

        try:
            print("DEBUG: start donation creation")
            donation = Donation(
                amount=donation_data.amount,
                donor_id=donor_id,
                project_id=donation_data.project_id,
                status=TransactionStatus.PENDING,
                is_anonymous=donation_data.is_anonymous,
                gas_fee=0.01
            )
            self.db.add(donation)
            await self.db.commit()
            await self.db.refresh(donation)

            timestamp = str(int(datetime.now(CN_TZ).timestamp()))
            transaction_hash = self.blockchain.generate_transaction_hash(
                donor.wallet_address,
                project.blockchain_address,
                donation_data.amount,
                timestamp
            )
            print("DEBUG: transaction_hash =", transaction_hash)
            donation.transaction_hash = transaction_hash

            await self.db.flush()
            await self.db.refresh(donation)

            tx_data = TransactionData(
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
                    "timestamp": timestamp,
                }
            )
            print("DEBUG: tx_data =", tx_data)

            added = await self.blockchain.add_transaction_to_pool(tx_data)
            print("DEBUG: added_to_pool =", added)
            if added:
                donation.status = TransactionStatus.IN_POOL
                from decimal import Decimal
                donor.balance = donor.balance - (Decimal(str(donation_data.amount)) + Decimal(str(donation.gas_fee)))

                await self.db.commit()
                await self.db.refresh(donation)
                await self.db.refresh(donor)
                print("DEBUG: donation created =", donation)
                return donation
            else:
                await self.db.delete(donation)
                await self.db.commit()
                return None

        except Exception as e:
            print("ERROR in create_donation:", e)
            await self.db.rollback()
            return None

    async def get_donation(self, donation_id: int) -> Optional[Donation]:
        result = await self.db.execute(select(Donation).where(Donation.id == donation_id))
        return result.scalars().first()

    async def get_user_donations(self, user_id: int, page: int = 1, size: int = 10):
        stmt = select(Donation).where(Donation.donor_id == user_id)
        result = await self.db.execute(stmt)
        all_rows = result.scalars().all()
        total = len(all_rows)

        stmt = stmt.order_by(Donation.created_at.desc()).offset((page - 1) * size).limit(size)
        result = await self.db.execute(stmt)
        donations = result.scalars().all()

        return donations, total

    async def get_project_donations(self, project_id: int, page: int = 1, size: int = 10):
        stmt = select(Donation).where(
            Donation.project_id == project_id,
            Donation.status == TransactionStatus.CONFIRMED
        )
        result = await self.db.execute(stmt)
        all_rows = result.scalars().all()
        total = len(all_rows)

        stmt = stmt.order_by(Donation.created_at.desc()).offset((page - 1) * size).limit(size)
        result = await self.db.execute(stmt)
        donations = result.scalars().all()

        return donations, total

    async def confirm_donation(self, transaction_hash: str, block_hash: str, block_number: int) -> bool:
        print("DEBUG: confirm_donation called with tx =", transaction_hash)
        result = await self.db.execute(
            select(Donation).where(Donation.transaction_hash == transaction_hash)
        )
        donation = result.scalars().first()
        if not donation:
            print("DEBUG: confirm_donation donation not found for tx =", transaction_hash)
            return False

        try:
            donation.status = TransactionStatus.CONFIRMED
            donation.block_hash = block_hash
            donation.block_number = block_number
            donation.confirmed_at = datetime.now(CN_TZ)

            # 更新项目已筹金额
            result = await self.db.execute(
                select(Project).where(Project.id == donation.project_id)
            )
            project = result.scalars().first()
            if project:
                print(
                    "DEBUG: before update project.current_amount =",
                    project.current_amount,
                    "donation.amount =",
                    donation.amount,
                )
                current = project.current_amount

                # 统一成 Decimal 处理，避免 Decimal 与 float 混算报错
                if current is None:
                    current = Decimal("0")

                if isinstance(current, Decimal):
                    add_value = (
                        donation.amount
                        if isinstance(donation.amount, Decimal)
                        else Decimal(str(donation.amount))
                    )
                    project.current_amount = current + add_value
                else:
                    # 如果 current 不是 Decimal（例如 float），退化为 float 计算
                    project.current_amount = float(current or 0) + float(donation.amount)

                print(
                    "DEBUG: after update project.current_amount =",
                    project.current_amount,
                )

            await self.db.commit()
            return True

        except Exception as e:
            print("ERROR in confirm_donation:", e)
            await self.db.rollback()
            return False

    async def get_donation_statistics(self, project_id: Optional[int] = None) -> dict:
        stmt = select(Donation).where(Donation.status == TransactionStatus.CONFIRMED)
        if project_id:
            stmt = stmt.where(Donation.project_id == project_id)

        result = await self.db.execute(stmt)
        rows = result.scalars().all()
        total_count = len(rows)
        total_amount = sum([d.amount for d in rows]) if total_count > 0 else 0

        return {
            "total_amount": total_amount,
            "total_count": total_count,
            "average_amount": total_amount / total_count if total_count > 0 else 0
        }
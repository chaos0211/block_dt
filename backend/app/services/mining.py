import time
import threading
from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.block_chain import Block, Transaction, TransactionPool
from app.db.models.donation import Donation, TransactionStatus
from app.schemas.block_chain import TransactionData, BlockData, MiningResult
from app.services.block_chain import BlockchainService
from app.services.donation import DonationService
from app.core.config import settings
import json
from datetime import datetime, timedelta, timezone
CN_TZ = timezone(timedelta(hours=8))


class MiningService:
    def __init__(self, db: AsyncSession):
        # 使用异步会话进行所有数据库操作
        self.db = db
        # BlockchainService 仅用于纯计算方法（如 calculate_merkle_root、validate_block），，
        # 不再依赖其内部的同步 DB 调用
        self.blockchain = BlockchainService(None)
        self.donation_service = DonationService(db)
        self.is_mining = False

    async def mine_block(self, miner_address: str, max_transactions: int = 10) -> MiningResult:
        """挖矿操作（异步版）"""
        if self.is_mining:
            return MiningResult(success=False)

        self.is_mining = True
        start_time = time.time()

        try:
            # 1. 获取待处理交易（从交易池异步查询）
            stmt_pool = (
                select(TransactionPool)
                .order_by(
                    TransactionPool.priority_score.desc(),
                    TransactionPool.created_at.asc(),
                )
                .limit(max_transactions)
            )
            result_pool = await self.db.execute(stmt_pool)
            pool_transactions = list(result_pool.scalars().all())

            if not pool_transactions:
                return MiningResult(success=False)

            # 将 TransactionPool 记录转换为 TransactionData
            pending_transactions: List[TransactionData] = []
            for pool_tx in pool_transactions:
                data = json.loads(pool_tx.data) if pool_tx.data else {}
                if not isinstance(data, dict):
                    data = {}
                tx_type = data.get("tx_type") or data.get("transaction_type") or "donation"

                pending_transactions.append(
                    TransactionData(
                        transaction_hash=pool_tx.transaction_hash,
                        from_address=pool_tx.from_address,
                        to_address=pool_tx.to_address,
                        amount=pool_tx.amount,
                        transaction_type=tx_type,
                        gas_fee=pool_tx.gas_fee,
                        data=data,
                    )
                )

            # 2. 获取最新区块，如不存在则创建创世区块
            stmt_last_block = select(Block).order_by(Block.block_number.desc()).limit(1)
            result_last_block = await self.db.execute(stmt_last_block)
            latest_block: Optional[Block] = result_last_block.scalars().first()

            if not latest_block:
                # 创建创世区块
                genesis_number = 1
                genesis_timestamp = datetime.now(CN_TZ)
                header = {
                    "block_number": genesis_number,
                    "previous_hash": "1",
                    "timestamp": genesis_timestamp.isoformat(),
                    "tx_hashes": [],
                    "miner_address": "system_genesis",
                    "nonce": 0,
                    "difficulty": 0,
                }
                genesis_block_hash = self.blockchain._hash_block_header(header) if hasattr(self.blockchain, "_hash_block_header") else "GENESIS"

                genesis_block = Block(
                    block_number=genesis_number,
                    block_hash=genesis_block_hash,
                    previous_hash="1",
                    merkle_root=self.blockchain.calculate_merkle_root([]),
                    nonce=0,
                    difficulty=0,
                    miner_address="system_genesis",
                    reward=0.0,
                    transaction_count=0,
                )
                self.db.add(genesis_block)
                await self.db.commit()
                await self.db.refresh(genesis_block)
                latest_block = genesis_block

            # 3. 准备新区块数据
            new_block_number = latest_block.block_number + 1
            previous_hash = latest_block.block_hash
            timestamp = datetime.now(CN_TZ)

            block_data = BlockData(
                block_number=new_block_number,
                previous_hash=previous_hash,
                transactions=pending_transactions,
                timestamp=timestamp,
                miner_address=miner_address,
            )

            # 4. 计算默克尔根
            merkle_root = self.blockchain.calculate_merkle_root(pending_transactions)

            # 5. 挖矿 - 寻找符合难度要求的 nonce
            nonce = 0
            while True:
                is_valid, block_hash = self.blockchain.validate_block(
                    block_data, nonce, previous_hash
                )
                if is_valid:
                    break
                nonce += 1
                if nonce > 1000000:
                    return MiningResult(success=False)

            # 6. 创建新区块
            new_block = Block(
                block_number=new_block_number,
                block_hash=block_hash,
                previous_hash=previous_hash,
                merkle_root=merkle_root,
                nonce=nonce,
                difficulty=self.blockchain.difficulty,
                miner_address=miner_address,
                reward=settings.mining_reward,
                transaction_count=len(pending_transactions),
            )
            self.db.add(new_block)

            # 7. 处理区块中的交易
            for tx_data in pending_transactions:
                # 创建确认的交易记录
                transaction = Transaction(
                    transaction_hash=tx_data.transaction_hash,
                    from_address=tx_data.from_address,
                    to_address=tx_data.to_address,
                    amount=tx_data.amount,
                    transaction_type=tx_data.transaction_type,
                    block_hash=block_hash,
                    block_number=new_block_number,
                    gas_fee=tx_data.gas_fee,
                    data=json.dumps(tx_data.data) if tx_data.data else None,
                    is_confirmed=True,
                    confirmed_at=datetime.now(CN_TZ),
                )
                self.db.add(transaction)

                # 确认对应的捐赠交易
                if tx_data.transaction_type == "donation":
                    await self.donation_service.confirm_donation(
                        tx_data.transaction_hash,
                        block_hash,
                        new_block_number,
                    )

                # 处理项目创世交易（项目上链）
                if tx_data.transaction_type == "project_creation":
                    try:
                        project_id = None
                        if isinstance(tx_data.data, dict):
                            project_id = tx_data.data.get("project_id")
                        if project_id:
                            from app.db.models.projects import Project
                            stmt_project = select(Project).where(Project.id == project_id)
                            result_project = await self.db.execute(stmt_project)
                            project = result_project.scalars().first()
                            if project:
                                project.status = "on_chain"
                                project.blockchain_tx_hash = tx_data.transaction_hash
                                project.on_chain_at = datetime.now(CN_TZ)
                                project.blockchain_address = tx_data.to_address
                    except Exception:
                        # 项目状态更新失败不影响区块落库
                        pass

                # 从交易池中移除已确认的交易
                await self.db.execute(
                    delete(TransactionPool).where(
                        TransactionPool.transaction_hash == tx_data.transaction_hash
                    )
                )

            # 8. 给矿工发放奖励（占位实现）
            await self._reward_miner(miner_address, settings.mining_reward)

            await self.db.commit()

            mining_time = time.time() - start_time

            return MiningResult(
                success=True,
                block_hash=block_hash,
                nonce=nonce,
                mining_time=mining_time,
                transactions_count=len(pending_transactions),
                reward=settings.mining_reward,
            )

        except Exception:
            await self.db.rollback()
            return MiningResult(success=False)

        finally:
            self.is_mining = False

    async def _reward_miner(self, miner_address: str, reward: float):
        """给矿工发放奖励（异步占位）"""
        # TODO: 如果未来需要将奖励记录在链上或账户表中，可以在此编写异步逻辑
        return None

    def start_auto_mining(self, miner_address: str, interval: int = 30):
        """启动自动挖矿"""

        def mining_loop():
            while True:
                try:
                    # 检查是否有待处理交易
                    pending_count = self.db.query(TransactionPool).count()

                    if pending_count > 0:
                        result = self.mine_block(miner_address)
                        if result.success:
                            print(f"挖矿成功: 区块哈希 {result.block_hash}, "
                                  f"处理交易数 {result.transactions_count}")

                    time.sleep(interval)

                except Exception as e:
                    print(f"自动挖矿错误: {e}")
                    time.sleep(interval)

        mining_thread = threading.Thread(target=mining_loop, daemon=True)
        mining_thread.start()

    def get_mining_statistics(self) -> dict:
        """获取挖矿统计信息"""
        total_blocks = self.db.query(Block).count()

        latest_block = self.blockchain.get_latest_block()
        latest_block_time = latest_block.timestamp if latest_block else None

        pending_transactions = self.db.query(TransactionPool).count()

        return {
            "total_blocks": total_blocks,
            "latest_block_time": latest_block_time,
            "pending_transactions": pending_transactions,
            "is_mining": self.is_mining
        }
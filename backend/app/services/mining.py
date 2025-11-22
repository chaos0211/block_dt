import time
import threading
from typing import List, Optional
from sqlalchemy.orm import Session
from ..models.blockchain import Block, Transaction, TransactionPool
from ..models.donation import Donation, TransactionStatus
from ..schemas.blockchain import TransactionData, BlockData, MiningResult
from .blockchain_service import BlockchainService
from .donation_service import DonationService
from ..config import settings
import json
from datetime import datetime


class MiningService:
    def __init__(self, db: Session):
        self.db = db
        self.blockchain = BlockchainService(db)
        self.donation_service = DonationService(db)
        self.is_mining = False

    def mine_block(self, miner_address: str, max_transactions: int = 10) -> MiningResult:
        """挖矿操作"""
        if self.is_mining:
            return MiningResult(success=False)

        self.is_mining = True
        start_time = time.time()

        try:
            # 获取待处理交易
            pending_transactions = self.blockchain.get_pending_transactions(max_transactions)

            if not pending_transactions:
                return MiningResult(
                    success=False
                )

            # 获取最新区块
            latest_block = self.blockchain.get_latest_block()
            if not latest_block:
                # 创建创世区块
                latest_block = self.blockchain.create_genesis_block()

            # 准备新区块数据
            new_block_number = latest_block.block_number + 1
            previous_hash = latest_block.block_hash
            timestamp = datetime.utcnow()

            block_data = BlockData(
                block_number=new_block_number,
                previous_hash=previous_hash,
                transactions=pending_transactions,
                timestamp=timestamp,
                miner_address=miner_address
            )

            # 计算默克尔根
            merkle_root = self.blockchain.calculate_merkle_root(pending_transactions)

            # 挖矿 - 寻找符合难度要求的nonce
            nonce = 0
            while True:
                is_valid, block_hash = self.blockchain.validate_block(
                    block_data, nonce, previous_hash
                )

                if is_valid:
                    break

                nonce += 1

                # 防止无限循环，设置最大尝试次数
                if nonce > 1000000:
                    return MiningResult(success=False)

            # 创建新区块
            new_block = Block(
                block_number=new_block_number,
                block_hash=block_hash,
                previous_hash=previous_hash,
                merkle_root=merkle_root,
                nonce=nonce,
                difficulty=self.blockchain.difficulty,
                miner_address=miner_address,
                reward=settings.mining_reward,
                transaction_count=len(pending_transactions)
            )

            # 保存区块到数据库
            self.db.add(new_block)

            # 处理区块中的交易
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
                    confirmed_at=datetime.utcnow()
                )

                self.db.add(transaction)

                # 确认对应的捐赠交易
                if tx_data.transaction_type == "donation":
                    self.donation_service.confirm_donation(
                        tx_data.transaction_hash,
                        block_hash,
                        new_block_number
                    )

                # 从交易池中移除已确认的交易
                self.db.query(TransactionPool).filter(
                    TransactionPool.transaction_hash == tx_data.transaction_hash
                ).delete()

            # 给矿工发放奖励
            self._reward_miner(miner_address, settings.mining_reward)

            self.db.commit()

            mining_time = time.time() - start_time

            return MiningResult(
                success=True,
                block_hash=block_hash,
                nonce=nonce,
                mining_time=mining_time,
                transactions_count=len(pending_transactions),
                reward=settings.mining_reward
            )

        except Exception as e:
            self.db.rollback()
            return MiningResult(success=False)

        finally:
            self.is_mining = False

    def _reward_miner(self, miner_address: str, reward: float):
        """给矿工发放奖励"""
        # 这里可以实现给矿工发放代币奖励的逻辑
        # 暂时简化处理
        pass

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
import hashlib
import json
import time
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.db.models.block_chain import Block, Transaction, TransactionPool
from app.db.models.donation import Donation, TransactionStatus
from app.schemas.block_chain import TransactionData, BlockData, MiningResult
from app.core.config import settings   # 这里的settings 是
import uuid


class BlockchainService:
    def __init__(self, db: Session):
        self.db = db
        self.difficulty = settings.blockchain_difficulty

    def generate_hash(self, data: str) -> str:
        """生成SHA-256哈希值"""
        return hashlib.sha256(data.encode()).hexdigest()

    def generate_transaction_hash(self, from_addr: str, to_addr: str,
                                  amount: float, timestamp: str) -> str:
        """生成交易哈希"""
        data = f"{from_addr}{to_addr}{amount}{timestamp}"
        return self.generate_hash(data)

    def create_genesis_block(self) -> Block:
        """创建创世区块"""
        genesis_block = Block(
            block_number=0,
            block_hash="0000000000000000000000000000000000000000000000000000000000000000",
            previous_hash="0",
            merkle_root="genesis",
            nonce=0,
            difficulty=self.difficulty,
            miner_address="system",
            reward=0.0,
            transaction_count=0
        )

        self.db.add(genesis_block)
        self.db.commit()
        return genesis_block

    def get_latest_block(self) -> Optional[Block]:
        """获取最新区块"""
        return self.db.query(Block).order_by(Block.block_number.desc()).first()

    def calculate_merkle_root(self, transactions: List[TransactionData]) -> str:
        """计算交易的默克尔根"""
        if not transactions:
            return "0"

        tx_hashes = [tx.transaction_hash for tx in transactions]

        while len(tx_hashes) > 1:
            if len(tx_hashes) % 2 != 0:
                tx_hashes.append(tx_hashes[-1])

            new_level = []
            for i in range(0, len(tx_hashes), 2):
                combined = tx_hashes[i] + tx_hashes[i + 1]
                new_level.append(self.generate_hash(combined))

            tx_hashes = new_level

        return tx_hashes[0]

    def add_transaction_to_pool(self, transaction_data: TransactionData) -> bool:
        """添加交易到交易池"""
        try:
            # 计算优先级分数（基于gas费用）
            priority_score = transaction_data.gas_fee

            pool_transaction = TransactionPool(
                transaction_hash=transaction_data.transaction_hash,
                from_address=transaction_data.from_address,
                to_address=transaction_data.to_address,
                amount=transaction_data.amount,
                gas_fee=transaction_data.gas_fee,
                data=json.dumps(transaction_data.data) if transaction_data.data else None,
                priority_score=priority_score
            )

            self.db.add(pool_transaction)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            return False

    def get_pending_transactions(self, limit: int = 10) -> List[TransactionData]:
        """获取待处理交易（按优先级排序）"""
        pool_transactions = (
            self.db.query(TransactionPool)
            .order_by(TransactionPool.priority_score.desc(),
                      TransactionPool.created_at.asc())
            .limit(limit)
            .all()
        )

        transactions = []
        for pool_tx in pool_transactions:
            data = json.loads(pool_tx.data) if pool_tx.data else None
            transactions.append(TransactionData(
                transaction_hash=pool_tx.transaction_hash,
                from_address=pool_tx.from_address,
                to_address=pool_tx.to_address,
                amount=pool_tx.amount,
                transaction_type="donation",  # 默认类型
                gas_fee=pool_tx.gas_fee,
                data=data
            ))

        return transactions

    def validate_block(self, block_data: BlockData, nonce: int,
                       previous_hash: str) -> tuple[bool, str]:
        """验证区块"""
        # 构建区块字符串
        merkle_root = self.calculate_merkle_root(block_data.transactions)
        block_string = (
            f"{block_data.block_number}"
            f"{previous_hash}"
            f"{merkle_root}"
            f"{block_data.timestamp.isoformat()}"
            f"{nonce}"
        )

        # 计算哈希
        block_hash = self.generate_hash(block_string)

        # 验证难度
        target = "0" * self.difficulty
        is_valid = block_hash.startswith(target)

        return is_valid, block_hash


class ProjectBlockchainService:
    def __init__(self, db: Session, blockchain_service: BlockchainService):
        self.db = db
        self.blockchain = blockchain_service

    def create_project_address(self, project_id: int) -> str:
        """为项目创建区块链地址"""
        address_data = f"project_{project_id}_{int(time.time())}"
        return f"0x{hashlib.sha256(address_data.encode()).hexdigest()[:40]}"

    def put_project_on_chain(self, project_id: int, project_title: str,
                             target_amount: float) -> Optional[str]:
        """将项目信息上链"""
        try:
            # 创建项目上链交易
            project_address = self.create_project_address(project_id)
            timestamp = str(int(time.time()))

            transaction_data = TransactionData(
                transaction_hash=self.blockchain.generate_transaction_hash(
                    "system", project_address, 0.0, timestamp
                ),
                from_address="system",
                to_address=project_address,
                amount=0.0,
                transaction_type="project_creation",
                gas_fee=0.0,
                data={
                    "project_id": project_id,
                    "title": project_title,
                    "target_amount": target_amount,
                    "timestamp": timestamp
                }
            )

            # 直接创建交易记录（不消耗gas费用）
            transaction = Transaction(
                transaction_hash=transaction_data.transaction_hash,
                from_address=transaction_data.from_address,
                to_address=transaction_data.to_address,
                amount=transaction_data.amount,
                transaction_type=transaction_data.transaction_type,
                gas_fee=0.0,
                data=json.dumps(transaction_data.data),
                is_confirmed=True,
                confirmed_at=func.now()
            )

            self.db.add(transaction)
            self.db.commit()

            return project_address
        except Exception as e:
            self.db.rollback()
            return None
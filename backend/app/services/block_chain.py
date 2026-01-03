import hashlib
import json
import time
import math
from typing import List, Optional, Dict, Any

from sqlalchemy import func
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

    def estimate_gas_fee(
        self,
        *,
        tx_type: str,
        amount: float = 0.0,
        data: Optional[Dict[str, Any]] = None,
        pending_pool_size: int = 0,
    ) -> float:
        """估算 Gas 费用（教学/私链模拟版）。

        设计目标：
        - 可解释、可复现：同样输入得到同样输出
        - 拥堵越高（交易池越大）费用越高
        - 交易类型越“复杂”费用越高
        - data 越大（模拟 calldata/存储）费用越高
        - 金额越大（轻微影响）费用略高

        返回值单位：系统内部的“链内费用”数值（float），用于排序与展示。
        """
        try:
            safe_type = (tx_type or "donation").lower()

            # 1) 交易类型基础复杂度（模拟不同合约函数/指令复杂度）
            base_units_map: Dict[str, float] = {
                "donation": 21000.0,
                "project_creation": 32000.0,
                "fund_usage": 26000.0,
                "project_update": 24000.0,
            }
            base_units = base_units_map.get(safe_type, 21000.0)

            # 2) 拥堵因子：池子越大，费用越高（封顶，避免离谱）
            p = max(0, int(pending_pool_size))
            congestion = 1.0 + min(1.5, p / 20.0)  # 0->1.0, 20->2.0, 30+ capped at 2.5

            # 3) data 大小因子：JSON 序列化后的字节数（封顶）
            payload = data if isinstance(data, dict) else {}
            try:
                data_bytes = len(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8"))
            except Exception:
                data_bytes = 0
            data_factor = 1.0 + min(0.8, data_bytes / 2048.0)  # 0B->1.0, 2KB->2.0, capped at 1.8

            # 4) 金额因子：轻微增加（避免金额主导费用）
            a = float(amount or 0.0)
            if a < 0:
                a = 0.0
            amount_factor = 1.0 + min(0.5, (math.log10(1.0 + a) / 10.0))

            # 5) 模拟 EIP-1559：base fee + tip（随拥堵上升）
            base_gwei = 12.0
            tip_gwei = 1.0 + min(3.0, p / 15.0)
            gas_price_gwei = base_gwei * congestion + tip_gwei

            # 6) 估算 gas used & fee
            gas_units = base_units * congestion * data_factor * amount_factor

            # 将 gwei 转换为“链内费用”（保持数值可读）
            fee = gas_units * gas_price_gwei * 1e-9

            # 7) 约束范围：避免过小/过大导致展示不合理
            fee = max(0.00001, min(0.02, fee))

            return float(round(fee, 8))
        except Exception:
            # 兜底：任何异常返回一个小的合理值
            return 0.00001

    async def create_genesis_block(self) -> Block:
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
        await self.db.commit()
        return genesis_block

    async def get_latest_block(self) -> Optional[Block]:
        """获取最新区块"""
        result = await self.db.execute(
            Block.__table__.select().order_by(Block.block_number.desc()).limit(1)
        )
        row = result.first()
        return row[0] if row else None

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

    async def add_transaction_to_pool(self, transaction_data: TransactionData) -> bool:
        """添加交易到交易池（async版本）"""
        try:
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
            await self.db.commit()
            print("DEBUG: add_transaction_to_pool success:", transaction_data.transaction_hash)
            return True
        except Exception as e:
            print("ERROR: add_transaction_to_pool failed:", e)
            await self.db.rollback()
            return False

    async def get_pending_transactions(self, limit: int = 10) -> List[TransactionData]:
        """获取待处理交易（按优先级排序）"""
        result = await self.db.execute(
            TransactionPool.__table__
            .select()
            .order_by(TransactionPool.priority_score.desc(),
                      TransactionPool.created_at.asc())
            .limit(limit)
        )
        pool_transactions = result.fetchall()

        transactions: List[TransactionData] = []
        for row in pool_transactions:
            pool_tx = row[0] if isinstance(row, tuple) else row
            # data 中可以包含 tx_type / transaction_type 等字段
            data = json.loads(pool_tx.data) if pool_tx.data else {}
            if not isinstance(data, dict):
                data = {}

            tx_type = data.get("tx_type") or data.get("transaction_type") or "donation"

            transactions.append(TransactionData(
                transaction_hash=pool_tx.transaction_hash,
                from_address=pool_tx.from_address,
                to_address=pool_tx.to_address,
                amount=pool_tx.amount,
                transaction_type=tx_type,
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

    async def put_project_on_chain(self, project_id: int, project_title: str,
                                   target_amount: float) -> Optional[str]:
        """将项目信息提交到交易池，等待挖矿打包上链。

        此处只负责构造 project_creation 类型的创世交易并写入 TransactionPool，
        不直接创建已确认的 Transaction 记录，也不写入区块。
        """
        try:
            # 为项目生成链上地址
            project_address = self.create_project_address(project_id)
            timestamp = str(int(time.time()))

            # 在 data 中显式带上 tx_type，方便后续从交易池解析
            data: Dict[str, Any] = {
                "tx_type": "project_creation",
                "project_id": project_id,
                "title": project_title,
                "target_amount": target_amount,
                "timestamp": timestamp,
            }

            transaction_data = TransactionData(
                transaction_hash=self.blockchain.generate_transaction_hash(
                    "system", project_address, 0.0, timestamp
                ),
                from_address="system",
                to_address=project_address,
                amount=0.0,
                transaction_type="project_creation",
                gas_fee=0.0,
                data=data,
            )

            # 将创世交易加入交易池，等待后续挖矿
            added = await self.blockchain.add_transaction_to_pool(transaction_data)
            if not added:
                return None

            # 此处不修改 Project 状态，也不在此创建 Transaction；
            # 由后续挖矿逻辑负责从交易池取出该交易，打包进区块并写入 transactions 表。
            return project_address
        except Exception:
            # 发生异常时回滚数据库会话
            await self.db.rollback()
            return None
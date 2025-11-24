import hashlib
import json
import time
from typing import List, Optional

from sqlalchemy import select, desc
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.block_chain import Block, Transaction, TransactionPool


def _sha256(data: str) -> str:
    """Helper: SHA-256 哈希函数。"""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def calculate_merkle_root(tx_hashes: List[str]) -> str:
    """根据一组交易哈希计算简单的 Merkle Root（简化版）。

    - 如果没有交易，则以固定字符串 "empty" 作为种子；
    - 使用两两配对、哈希拼接的方式逐层向上计算；
    """
    if not tx_hashes:
        return _sha256("empty")

    layer = tx_hashes[:]
    while len(layer) > 1:
        new_layer = []
        for i in range(0, len(layer), 2):
            left = layer[i]
            right = layer[i + 1] if i + 1 < len(layer) else layer[i]
            new_layer.append(_sha256(left + right))
        layer = new_layer
    return layer[0]


class BlockchainDB:
    """纯基于数据库的区块链记账实现（异步版）。

    **设计要点：**
    - 不再维护内存中的链状态（无 self.chain / self.current_transactions）；
    - 所有待打包交易记录在 TransactionPool 表；
    - 已确认交易记录在 Transaction 表；
    - 区块头信息记录在 Block 表；
    - 本类不创建引擎或会话，完全依赖外部传入的 AsyncSession。
    """

    def __init__(self) -> None:
        # 不持有 Session、不创建 engine，所有会话由上层（FastAPI 依赖注入）提供
        pass

    # ---------- 交易相关：写入交易池 ----------

    async def new_transaction(
        self,
        db: AsyncSession,
        sender: str,
        recipient: str,
        amount: float,
        tx_type: str = "TRANSFER",
        payload: Optional[dict] = None,
        priority_score: float = 1.0,
    ) -> str:
        """创建一笔新交易，写入 transaction_pool 表，等待后续挖矿打包。

        :param db: AsyncSession（由上层注入，例如 get_session 产生的会话）
        :param sender: 发送方地址
        :param recipient: 接收方地址
        :param amount: 金额
        :param tx_type: 交易类型，如 PROJECT_INIT、DONATION 等
        :param payload: 附加业务数据，例如项目 ID、标题等
        :param priority_score: 优先级（可用于选择打包顺序）
        :return: 交易哈希（tx_hash）
        """
        tx = {
            "type": tx_type,
            "sender": sender,
            "recipient": recipient,
            "amount": float(amount),
            "payload": payload or {},
            "timestamp": time.time(),
        }

        # 基于完整交易内容生成稳定的交易哈希
        tx_str = json.dumps(tx, sort_keys=True, separators=(",", ":"))
        tx_hash = _sha256(tx_str)

        pool_tx = TransactionPool(
            transaction_hash=tx_hash,
            from_address=sender,
            to_address=recipient,
            amount=float(amount),
            gas_fee=0.0,
            data=tx_str,
            priority_score=priority_score,
        )
        db.add(pool_tx)
        await db.commit()
        # 不强制 refresh：通常不需要回读 pool_tx
        return tx_hash

    # ---------- 区块相关：查询最新区块 / 创建创世区块 ----------

    async def _get_latest_block(self, db: AsyncSession) -> Optional[Block]:
        """获取当前链上的最新区块（按 block_number 降序）。"""
        stmt = select(Block).order_by(desc(Block.block_number))
        result = await db.execute(stmt)
        return result.scalars().first()

    async def _create_genesis_block(self, db: AsyncSession) -> Block:
        """创建创世区块（如果不存在）。"""
        existing = await self._get_latest_block(db)
        if existing is not None:
            return existing

        timestamp = time.time()
        header = {
            "block_number": 1,
            "timestamp": timestamp,
            "tx_hashes": [],
            "previous_hash": "1",  # 创世块前一个哈希约定为 "1"
            "nonce": 0,
            "difficulty": 0,
            "miner_address": "system_genesis",
        }
        block_hash = _sha256(json.dumps(header, sort_keys=True, separators=(",", ":")))

        genesis = Block(
            block_number=1,
            block_hash=block_hash,
            previous_hash="1",
            merkle_root=calculate_merkle_root([]),
            nonce=0,
            difficulty=0,
            miner_address="system_genesis",
            reward=0.0,
            transaction_count=0,
        )
        db.add(genesis)
        await db.commit()
        await db.refresh(genesis)
        return genesis

    # ---------- 挖矿：从池中取交易 → 生成新区块 → 迁移交易 ----------

    async def mine_block(self, db: AsyncSession, miner_address: str = "system_miner") -> Optional[Block]:
        """从 transaction_pool 中取出交易，打包生成新区块，并写入 blocks + transactions。

        - 如果还没有区块，会先创建创世区块；
        - 所有被打包的交易会从 transaction_pool 删除，并写入 Transaction 表；
        - 项目创世交易（例如 tx_type = project_creation/PROJECT_INIT）可在上层解析 data 后更新项目状态。
        """
        # 1. 读取待打包交易（按优先级从高到低，id 从小到大）
        pending_stmt = select(TransactionPool).order_by(
            desc(TransactionPool.priority_score), TransactionPool.id
        )
        pending_result = await db.execute(pending_stmt)
        pending: List[TransactionPool] = list(pending_result.scalars().all())

        if not pending:
            return None

        # 2. 获取最新区块，如不存在则创建创世块
        latest_block = await self._get_latest_block(db)
        if latest_block is None:
            latest_block = await self._create_genesis_block(db)

        new_block_number = latest_block.block_number + 1
        timestamp = time.time()

        # 3. 构建交易哈希列表与 Merkle Root
        tx_hashes: List[str] = [p.transaction_hash for p in pending]
        merkle_root = calculate_merkle_root(tx_hashes)

        # 简化版：nonce / difficulty 不做真正 PoW，仅作为占位字段
        nonce = 0
        difficulty = 0

        header = {
            "block_number": new_block_number,
            "timestamp": timestamp,
            "tx_hashes": tx_hashes,
            "previous_hash": latest_block.block_hash,
            "nonce": nonce,
            "difficulty": difficulty,
            "miner_address": miner_address,
        }
        block_hash = _sha256(json.dumps(header, sort_keys=True, separators=(",", ":")))

        # 4. 创建新区块记录
        new_block = Block(
            block_number=new_block_number,
            block_hash=block_hash,
            previous_hash=latest_block.block_hash,
            merkle_root=merkle_root,
            nonce=nonce,
            difficulty=difficulty,
            miner_address=miner_address,
            reward=0.0,
            transaction_count=len(pending),
        )
        db.add(new_block)

        # 5. 将交易从池中迁移到 Transaction 表
        for pool_tx in pending:
            # 解析 data 字段（其中可以包含 type/payload 等业务信息）
            try:
                data = json.loads(pool_tx.data) if pool_tx.data else {}
            except Exception:
                data = {}

            tx_type = None
            if isinstance(data, dict) and "type" in data:
                tx_type = data.get("type")

            transaction = Transaction(
                transaction_hash=pool_tx.transaction_hash,
                from_address=pool_tx.from_address,
                to_address=pool_tx.to_address,
                amount=pool_tx.amount,
                transaction_type=tx_type or "UNKNOWN",
                gas_fee=pool_tx.gas_fee,
                data=pool_tx.data,
                is_confirmed=True,
                confirmed_at=func.now(),
            )
            db.add(transaction)
            # 从交易池删除该交易
            await db.delete(pool_tx)

        await db.commit()
        await db.refresh(new_block)
        return new_block


# 提供一个便捷的全局操作入口，但不会持有任何内存链状态
blockchain_db = BlockchainDB()


__all__ = ["BlockchainDB", "blockchain_db", "calculate_merkle_root"]
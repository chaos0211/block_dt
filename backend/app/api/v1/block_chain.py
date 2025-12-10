from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.base import get_session as get_db
from app.schemas.block_chain import MiningResult, TransactionPoolStatus
from app.services.mining import MiningService

router = APIRouter(prefix="/api/v1/blockchain", tags=["auth"])



@router.post("/mine", response_model=MiningResult)
async def mine_block(
        miner_address: str,
        max_transactions: int = 10,
        db: AsyncSession = Depends(get_db)
):
    """手动挖矿"""
    service = MiningService(db)
    result = await service.mine_block(miner_address, max_transactions)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="挖矿失败，可能没有待处理交易或系统正在挖矿中"
        )

    return result



@router.get("/transaction-pool", response_model=TransactionPoolStatus)
async def get_transaction_pool_status(
        db: AsyncSession = Depends(get_db)
):
    """获取交易池状态（基于异步会话）"""
    from app.db.models.block_chain import TransactionPool

    # 统计待处理交易数量
    stmt_count = select(func.count()).select_from(TransactionPool)
    result_count = await db.execute(stmt_count)
    pending_transactions = result_count.scalar() or 0

    # 统计交易总金额
    stmt_total = select(func.sum(TransactionPool.amount))
    result_total = await db.execute(stmt_total)
    total_value = result_total.scalar() or 0

    # 统计平均 gas 费
    stmt_avg = select(func.avg(TransactionPool.gas_fee))
    result_avg = await db.execute(stmt_avg)
    avg_gas_fee = result_avg.scalar() or 0

    return TransactionPoolStatus(
        pending_transactions=pending_transactions,
        total_value=total_value,
        average_gas_fee=avg_gas_fee,
    )


# 新增：交易池明细列表接口
@router.get("/transaction-pool/list")
async def get_transaction_pool_list(
        page: int = 1,
        limit: int = 10,
        db: AsyncSession = Depends(get_db)
):
    """
    获取交易池明细列表（分页）
    返回结构：{"items": [...], "total": int}
    """
    from app.db.models.block_chain import TransactionPool

    # 统计总数
    stmt_count = select(func.count()).select_from(TransactionPool)
    result_count = await db.execute(stmt_count)
    total = result_count.scalar() or 0

    # 分页查询
    stmt_list = (
        select(TransactionPool)
        .order_by(TransactionPool.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    result_list = await db.execute(stmt_list)
    items = result_list.scalars().all()

    # 序列化为普通 dict，便于前端使用
    serialized_items = []
    for tx in items:
        serialized_items.append({
            "id": tx.id,
            "transaction_hash": tx.transaction_hash,
            "from_address": tx.from_address,
            "to_address": tx.to_address,
            "amount": tx.amount,
            "gas_fee": tx.gas_fee,
            "data": tx.data,
            "priority_score": tx.priority_score,
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
        })

    return {
        "items": serialized_items,
        "total": total,
    }


@router.get("/mining/statistics")
async def get_mining_statistics(
        db: AsyncSession = Depends(get_db)
):
    """获取挖矿统计信息（异步版，直接基于区块和交易表统计）"""
    from app.db.models.block_chain import Block, Transaction

    # 区块总数
    stmt_block_count = select(func.count()).select_from(Block)
    result_block_count = await db.execute(stmt_block_count)
    total_blocks = result_block_count.scalar() or 0

    # 交易总数
    stmt_tx_count = select(func.count()).select_from(Transaction)
    result_tx_count = await db.execute(stmt_tx_count)
    total_transactions = result_tx_count.scalar() or 0

    # 最新区块信息
    stmt_last_block = select(Block).order_by(Block.block_number.desc()).limit(1)
    result_last_block = await db.execute(stmt_last_block)
    last_block = result_last_block.scalars().first()

    latest_block_number = last_block.block_number if last_block else None
    latest_block_hash = last_block.block_hash if last_block else None

    return {
        "total_blocks": total_blocks,
        "total_transactions": total_transactions,
        "latest_block_number": latest_block_number,
        "latest_block_hash": latest_block_hash,
    }


@router.get("/chain-info")
async def get_chain_info(
        db: AsyncSession = Depends(get_db)
):
    """
    获取区块链综合信息：
    - total_blocks: 区块总数
    - height: 当前区块高度（total_blocks - 1，若有创世块）
    - total_transactions: 链上交易总数
    - pending_pool_size: 交易池中待处理交易数量
    - latest_block: 最新区块的关键信息
    - chain_valid: 简单链校验结果（当前版本始终返回 True）
    """
    from app.db.models.block_chain import Block, Transaction, TransactionPool

    # 区块总数
    stmt_block_count = select(func.count()).select_from(Block)
    result_block_count = await db.execute(stmt_block_count)
    total_blocks = result_block_count.scalar() or 0

    # 交易总数
    stmt_tx_count = select(func.count()).select_from(Transaction)
    result_tx_count = await db.execute(stmt_tx_count)
    total_transactions = result_tx_count.scalar() or 0

    # 交易池待处理数量
    stmt_pool_count = select(func.count()).select_from(TransactionPool)
    result_pool_count = await db.execute(stmt_pool_count)
    pending_pool_size = result_pool_count.scalar() or 0

    # 最新区块信息
    stmt_last_block = select(Block).order_by(Block.block_number.desc()).limit(1)
    result_last_block = await db.execute(stmt_last_block)
    last_block = result_last_block.scalars().first()

    latest_block = None
    if last_block:
        latest_block = {
            "block_number": last_block.block_number,
            "block_hash": last_block.block_hash,
            "previous_hash": last_block.previous_hash,
            "transactions_count": last_block.transaction_count,
            "timestamp": last_block.timestamp.isoformat() if last_block.timestamp else None,
            "miner_address": last_block.miner_address,
        }

    # 当前高度：如果有创世块（通常 block_number 从 0 开始），高度为 total_blocks - 1，否则为 0
    if total_blocks > 0:
        height = total_blocks - 1
    else:
        height = 0

    # 当前版本不做复杂链校验，先返回 True，后续可扩展为逐块校验 previous_hash / merkle_root 等
    chain_valid = True

    return {
        "total_blocks": total_blocks,
        "height": height,
        "total_transactions": total_transactions,
        "pending_pool_size": pending_pool_size,
        "latest_block": latest_block,
        "chain_valid": chain_valid,
    }


@router.get("/info")
async def get_blockchain_info(
        db: AsyncSession = Depends(get_db)
):
    """
    兼容前端使用的 /info 路由，内部复用 /chain-info 的实现
    """
    return await get_chain_info(db)


@router.post("/mining/start")
async def start_auto_mining(
        miner_address: str,
        interval: int = 30,
        db: AsyncSession = Depends(get_db)
):
    """启动自动挖矿（当前版本不支持，提示使用手动挖矿）"""
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="当前版本不支持自动挖矿，请使用 /api/v1/blockchain/mine 接口进行手动挖矿",
    )


@router.get("/blocks")
async def get_blocks(
        page: int = 1,
        limit: int = 10,
        db: AsyncSession = Depends(get_db)
):
    """分页获取链上区块"""
    from app.db.models.block_chain import Block

    # 统计总数
    stmt_count = select(func.count()).select_from(Block)
    result_count = await db.execute(stmt_count)
    total = result_count.scalar() or 0

    # 分页查询
    stmt_list = (
        select(Block)
        .order_by(Block.block_number.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    result_list = await db.execute(stmt_list)
    items = result_list.scalars().all()

    # 序列化
    serialized = []
    for b in items:
        serialized.append({
            "block_number": b.block_number,
            "block_hash": b.block_hash,
            "previous_hash": b.previous_hash,
            "transactions_count": b.transaction_count,
            "timestamp": b.timestamp.isoformat() if b.timestamp else None,
            "miner_address": b.miner_address
        })

    return {
        "items": serialized,
        "total": total
    }
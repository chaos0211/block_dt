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
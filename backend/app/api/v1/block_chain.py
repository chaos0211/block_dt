from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.base import get_session as get_db
from app.schemas.block_chain import MiningResult, TransactionPoolStatus
from app.services.mining import MiningService

router = APIRouter()


@router.post("/mine", response_model=MiningResult)
async def mine_block(
        miner_address: str,
        max_transactions: int = 10,
        db: Session = Depends(get_db)
):
    """手动挖矿"""
    service = MiningService(db)
    result = service.mine_block(miner_address, max_transactions)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="挖矿失败，可能没有待处理交易或系统正在挖矿中"
        )

    return result


@router.get("/transaction-pool", response_model=TransactionPoolStatus)
async def get_transaction_pool_status(
        db: Session = Depends(get_db)
):
    """获取交易池状态"""
    from app.db.models.block_chain import TransactionPool
    from sqlalchemy import func

    pending_transactions = db.query(TransactionPool).count()
    total_value = db.query(func.sum(TransactionPool.amount)).scalar() or 0
    avg_gas_fee = db.query(func.avg(TransactionPool.gas_fee)).scalar() or 0

    return TransactionPoolStatus(
        pending_transactions=pending_transactions,
        total_value=total_value,
        average_gas_fee=avg_gas_fee
    )


@router.get("/mining/statistics")
async def get_mining_statistics(
        db: Session = Depends(get_db)
):
    """获取挖矿统计信息"""
    service = MiningService(db)
    statistics = service.get_mining_statistics()

    return statistics


@router.post("/mining/start")
async def start_auto_mining(
        miner_address: str,
        interval: int = 30,
        db: Session = Depends(get_db)
):
    """启动自动挖矿"""
    service = MiningService(db)
    service.start_auto_mining(miner_address, interval)

    return {"message": f"自动挖矿已启动，挖矿间隔: {interval}秒"}
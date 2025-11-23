from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import get_db  # 假设你已经封装了 get_db
from . import schemas, services

app = FastAPI()


@app.post("/projects/publish", response_model=schemas.ProjectResponse)
def publish_project(request: schemas.ProjectCreateRequest, db: Session = Depends(get_db)):
    """
    发布项目接口：
    1. DB创建记录 (Pending)
    2. 区块链生成创世交易 (进入交易池)
    """
    return services.ProjectService.create_project_proposal(db, request)


@app.post("/blockchain/mine", response_model=schemas.MineResponse)
def mine_transactions(db: Session = Depends(get_db)):
    """
    手动打包接口：
    1. 挖矿打包交易
    2. 检查是否有 PROJECT_INIT 交易
    3. 将对应项目状态更新为 Active
    """
    result = services.MiningService.mine_block_and_sync_state(db)

    return schemas.MineResponse(
        message=result["message"],
        block_index=result.get("index", 0),
        transactions_count=result.get("transactions", 0),
        activated_projects=result["activated_projects"]
    )


@app.get("/blockchain/chain")
def get_chain():
    """查看完整区块链数据 (调试用)"""
    from .blockchain_core import blockchain_instance
    return {
        "chain": blockchain_instance.chain,
        "length": len(blockchain_instance.chain)
    }
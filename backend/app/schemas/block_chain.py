from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class TransactionData(BaseModel):
    transaction_hash: str
    from_address: str
    to_address: str
    amount: float
    transaction_type: str
    gas_fee: float
    data: Optional[Dict[str, Any]] = None

class BlockData(BaseModel):
    block_number: int
    previous_hash: str
    transactions: List[TransactionData]
    timestamp: datetime
    miner_address: str

class MiningResult(BaseModel):
    success: bool
    block_hash: Optional[str] = None
    nonce: Optional[int] = None
    mining_time: Optional[float] = None
    transactions_count: Optional[int] = None
    reward: Optional[float] = None

class TransactionPoolStatus(BaseModel):
    pending_transactions: int
    total_value: float
    average_gas_fee: float
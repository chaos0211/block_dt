from sqlalchemy import Column, Integer, ForeignKey, Numeric, String, Text, DateTime, func

from app.db.base import Base
class FundUsage(Base):
    __tablename__ = "fund_usages"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    amount = Column(Numeric(18, 8), nullable=False)

    # 使用说明
    usage_type = Column(String(64), nullable=False)          # 如：物资采购 / 医疗支出
    description = Column(Text, nullable=False)           # 具体用途说明

    # 凭证 & 证明材料（可以是 OSS / IPFS 地址）
    evidence_url = Column(String(64), nullable=True)         # 图片/文件的链接
    evidence_hash = Column(String(64), nullable=True)        # 凭证文件哈希，用于链上校验

    # 区块链相关
    transaction_hash = Column(String(64), unique=True, nullable=True)
    block_hash = Column(String(64), nullable=True)
    block_number = Column(Integer, nullable=True)
    gas_fee = Column(Numeric(18, 8), default=0)

    # 审核 & 时间
    status = Column(String(64), default="pending")  # pending / approved / rejected / on_chain
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
from sqlalchemy import Column, Integer, ForeignKey, Numeric, String, Text, DateTime, func

from app.db.base import Base
class ProjectUpdate(Base):
    __tablename__ = "project_updates"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    title = Column(String(64), nullable=False)          # 更新标题
    content = Column(Text, nullable=False)          # 文本说明
    attachments_url = Column(Text, nullable=True)   # 多个附件URL（JSON字符串）
    attachments_hash = Column(String(64), nullable=True)# 附件打包后的哈希

    # 上链信息
    transaction_hash = Column(String(64), unique=True, nullable=True)
    block_hash = Column(String(64), nullable=True)
    block_number = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
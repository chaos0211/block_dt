from pydantic import BaseModel
from typing import Optional


# 项目创建请求
class ProjectCreateRequest(BaseModel):
    title: str
    description: str
    target_amount: int


# 项目响应
class ProjectResponse(BaseModel):
    id: int
    title: str
    wallet_address: str
    status: str

    class Config:
        orm_mode = True


# 挖矿响应
class MineResponse(BaseModel):
    message: str
    block_index: int
    transactions_count: int
    activated_projects: list[int]  # 返回本次挖矿激活了哪些项目ID
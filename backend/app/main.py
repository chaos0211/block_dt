from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import auth, block_chain,donations, projects
from app.db.base import get_session
from app.services.block_chain import BlockchainService

app = FastAPI(title="Donate Chain API", version="0.1.0")

# 允许前端调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




# 注册路由
app.include_router(auth.router)
app.include_router(block_chain.router)
app.include_router(donations.router)
app.include_router(projects.router)
# app.include_router(apps.router)
# app.include_router(compare.router)
# app.include_router(predict.router)
# app.include_router(ads_hive.router)

@app.get("/health")
def health():
    return {"status": "ok"}

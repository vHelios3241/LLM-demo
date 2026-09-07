from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import close_db, init_db
from app.routers.auth import router as auth_router  # 新增

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据库连接，关闭时释放连接。"""
    await init_db()
    yield
    await close_db()

app = FastAPI(title="会议第二大脑 api", lifespan=lifespan)
app.include_router(auth_router)  # 挂载认证路由

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



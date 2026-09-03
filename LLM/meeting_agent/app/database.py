from tortoise import Tortoise
from app.config import settings

# 数据库配置信息
TORTOISE_ORM = {
    "connections": {
        "default": settings.DB_URL
    },
    "apps": {
        "models": {
            "models": [],
            "default_connection": "default",
        }
    }
}

async def init_db() -> None:
    # 初始化数据库连接
    await Tortoise.init(config=TORTOISE_ORM)
    # 生成数据库表结构
    await Tortoise.generate_schemas()

async def close_db() -> None:
    # 关闭数据库连接
    await Tortoise.close_connections()

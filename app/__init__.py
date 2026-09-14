from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routers import api_v1
from app.common.response import Success_response
from app.core.config import settings
from app.core.database import async_engine
from app.core.database_initializer import initialize_database
from app.core.exceptions import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """启动时初始化数据库，关闭时释放数据库连接池。"""
    # 开启自动迁移时，按“创建数据库 → 执行 Alembic 迁移”的顺序初始化。
    if settings.DATABASE_AUTO_MIGRATE:
        await initialize_database()

    # yield 之前属于启动阶段；执行到这里后，FastAPI 才开始接收请求。
    yield

    # 项目关闭时释放连接，避免连接一直占用 MySQL 资源。
    await async_engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_TITLE,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )
    # 注册错误处理
    register_exception_handlers(app)
    # 注册CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOW_ORIGINS,
        allow_credentials=settings.ALLOW_CREDENTIALS,
        allow_methods=settings.ALLOW_METHODS,
        allow_headers=settings.ALLOW_HEADERS,
    )

    @app.get("/")
    async def root():
        return Success_response(message="Hello World")

    app.include_router(api_v1)
    return app

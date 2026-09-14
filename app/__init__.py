from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routers import api_v1
from app.common.response import Success_response
from app.common.schema import MessageResponse
from app.core.config import settings
from app.core.database import async_engine
from app.core.database_initializer import initialize_database
from app.core.exceptions import register_exception_handlers


OPENAPI_TAGS = [
    {"name": "系统", "description": "服务状态与基础信息。"},
    {
        "name": "新闻模块",
        "description": "无需登录即可使用的新闻分类、列表和详情查询接口。",
    },
    {
        "name": "用户模块",
        "description": "用户注册、登录、资料维护和密码修改。",
    },
    {
        "name": "收藏模块",
        "description": "需要登录的新闻收藏查询与管理接口。",
    },
    {
        "name": "浏览历史模块",
        "description": "需要登录的新闻浏览历史记录与管理接口。",
    },
]


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
        description=(
            "移动端新闻资讯应用 REST API。提供新闻浏览、用户认证、收藏和浏览历史功能。"
            "\n\n受保护接口需在 `Authorization` 请求头中携带登录返回的 token。"
        ),
        debug=settings.DEBUG,
        lifespan=lifespan,
        openapi_tags=OPENAPI_TAGS,
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

    @app.get(
        "/",
        tags=["系统"],
        summary="检查服务状态",
        description="用于确认后端服务已经启动并可以正常响应请求。",
        response_model=MessageResponse,
        response_description="服务正常运行。",
        operation_id="checkServiceHealth",
    )
    async def root():
        return Success_response(message="Hello World")

    app.include_router(api_v1)
    return app

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


# 1.创建异步引擎
async_engine = create_async_engine(
    settings.ASYNC_DATABASE_URL,
    echo=settings.DATABASE_ECHO,  # 是否在控制台输出 SQL
    pool_size=settings.DATABASE_POOL_SIZE,  # 连接池保持的连接数量
    max_overflow=settings.DATABASE_MAX_OVERFLOW,  # 繁忙时增加的连接数量
)

# 需求：查询新闻功能的接口 → 依赖注入：创建依赖项获取数据库会话 + Depends 注入路由处理函数
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,  # 绑定数据库引擎
    class_=AsyncSession,  # 指定会话类
    expire_on_commit=False,  # 提交后会话不过期，不会重新查询数据库
)


# 依赖项
async def get_database() -> AsyncGenerator[AsyncSession, None]:
    """为一次请求提供异步数据库会话。"""
    async with AsyncSessionLocal() as session:
        try:
            yield session  # 返回数据库会话给路由处理函数
            await session.commit()  # 路由成功结束后统一提交事务
        except Exception:
            await session.rollback()  # 有异常，回滚
            raise
        finally:
            await session.close()  # 关闭会话

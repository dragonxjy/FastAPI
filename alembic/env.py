import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.base_model import Base
from app.core.config import settings

# 必须导入全部模型，它们才会登记到 Base.metadata。
from app.modules.news.model import Category, News  # noqa: F401
from app.modules.system.user.model import User, UserToken  # noqa: F401


# Alembic 运行命令时会把 alembic.ini 解析成这个对象。
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 自动生成迁移时，Alembic 会拿它和数据库进行比较。
target_metadata = Base.metadata
managed_tables = set(target_metadata.tables)


def include_object(object_, name, type_, reflected, compare_to) -> bool:
    """忽略没有对应 Model 的旧表，避免自动生成误删操作。"""
    if type_ == "table" and reflected and name not in managed_tables:
        return False
    return True


def configure_context(**kwargs) -> None:
    """集中设置在线和离线迁移共用的比较规则。"""
    context.configure(
        target_metadata=target_metadata,
        include_object=include_object,
        # 旧库使用了 unsigned 和 timestamp，先忽略历史类型差异。
        # 新增或删除字段仍然可以自动检测；类型变更应手动编写迁移。
        compare_type=False,
        **kwargs,
    )


def run_migrations_offline() -> None:
    """不连接数据库，只生成迁移 SQL。"""
    configure_context(
        url=settings.ASYNC_DATABASE_URL,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """在已经建立的数据库连接中执行迁移。"""
    configure_context(connection=connection)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """使用项目现有的 aiomysql 异步驱动连接数据库。"""
    configuration = config.get_section(config.config_ini_section, {})
    # 密码不写入 alembic.ini，始终从本地 .env.dev 读取。
    configuration["sqlalchemy.url"] = settings.ASYNC_DATABASE_URL
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # Alembic 核心是同步接口，通过 run_sync 复用异步连接。
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """启动异步迁移任务。"""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

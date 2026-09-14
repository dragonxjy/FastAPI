import asyncio
import re

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.base_model import Base
from app.core.config import BASE_DIR, settings

# 需要导入模型，Base.metadata 中才会登记对应的数据表。
from app.modules.news.model import Category, News  # noqa: F401
from app.modules.system.user.model import User, UserToken  # noqa: F401


DATABASE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")


async def create_database_if_not_exists() -> None:
    """先连接 MySQL 服务，在数据库不存在时创建它。"""
    database_name = settings.DATABASE_NAME
    # 数据库名不能作为普通 SQL 参数传入，因此先限制可用字符，避免拼接风险。
    if not DATABASE_NAME_PATTERN.fullmatch(database_name):
        raise ValueError("数据库名称只能包含字母、数字和下划线")

    # 这里只连接 MySQL 服务，不选择具体数据库。
    server_engine = create_async_engine(settings.ASYNC_DATABASE_SERVER_URL)
    try:
        async with server_engine.begin() as connection:
            # 已经存在时不会重复创建，也不会删除原来的数据库。
            await connection.execute(
                text(
                    f"CREATE DATABASE IF NOT EXISTS `{database_name}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            )
    finally:
        await server_engine.dispose()


def get_alembic_config() -> Config:
    """告诉 Alembic 配置文件和迁移目录分别在哪里。"""
    alembic_config = Config(str(BASE_DIR / "alembic.ini"))
    alembic_config.set_main_option("script_location", str(BASE_DIR / "alembic"))
    return alembic_config


def upgrade_database() -> None:
    """执行全部尚未运行的迁移，直到最新版本。"""
    command.upgrade(get_alembic_config(), "head")


def stamp_database() -> None:
    """已有表第一次接入 Alembic 时，只登记基线，不重复建表。"""
    command.stamp(get_alembic_config(), "head")


async def get_existing_schema() -> dict[str, set[str]]:
    """读取数据库中的表名及每张表已有的字段名。"""
    database_engine = create_async_engine(settings.ASYNC_DATABASE_URL)
    try:
        async with database_engine.connect() as connection:
            def inspect_schema(sync_connection) -> dict[str, set[str]]:
                database_inspector = inspect(sync_connection)
                return {
                    table_name: {
                        column["name"]
                        for column in database_inspector.get_columns(table_name)
                    }
                    for table_name in database_inspector.get_table_names()
                }

            # inspect 是同步接口，通过 run_sync 在异步连接中执行。
            return await connection.run_sync(inspect_schema)
    finally:
        await database_engine.dispose()


async def get_current_alembic_version(existing_tables: set[str]) -> str | None:
    """读取当前迁移版本；版本表不存在或没有记录时返回 None。"""
    if "alembic_version" not in existing_tables:
        return None

    database_engine = create_async_engine(settings.ASYNC_DATABASE_URL)
    try:
        async with database_engine.connect() as connection:
            return await connection.scalar(text("SELECT version_num FROM alembic_version"))
    finally:
        await database_engine.dispose()


def get_missing_structure(
    existing_schema: dict[str, set[str]],
) -> tuple[set[str], dict[str, set[str]]]:
    """比较 Model 与数据库，找出缺少的表和字段。"""
    model_schema = {
        table_name: set(table.columns.keys())
        for table_name, table in Base.metadata.tables.items()
    }
    missing_tables = set(model_schema) - set(existing_schema)
    missing_columns = {
        table_name: columns - existing_schema.get(table_name, set())
        for table_name, columns in model_schema.items()
        if table_name in existing_schema
        and columns - existing_schema[table_name]
    }
    return missing_tables, missing_columns


async def initialize_database() -> None:
    """先创建数据库，再用 Alembic 创建或升级表结构。"""
    # 第一步：保证 .env.dev 中配置的数据库已经存在。
    await create_database_if_not_exists()

    existing_schema = await get_existing_schema()
    model_tables = set(Base.metadata.tables)
    existing_model_tables = set(existing_schema) & model_tables
    current_version = await get_current_alembic_version(set(existing_schema))

    if current_version is not None:
        # 版本表中有记录，说明数据库已经正式由 Alembic 管理。
        await asyncio.to_thread(upgrade_database)
    elif not existing_model_tables:
        # 全新数据库没有业务表，首个迁移会创建完整表结构。
        await asyncio.to_thread(upgrade_database)
    elif model_tables.issubset(existing_schema):
        # 旧数据库第一次接入 Alembic，登记基线前先确认没有缺字段。
        _, missing_columns = get_missing_structure(existing_schema)
        if missing_columns:
            details = "; ".join(
                f"{table}: {', '.join(sorted(columns))}"
                for table, columns in sorted(missing_columns.items())
            )
            raise RuntimeError(f"已有数据表缺少字段，不能登记基线：{details}")
        await asyncio.to_thread(stamp_database)
    else:
        # 只存在部分业务表时停止，避免迁移与人工表结构互相覆盖。
        missing_tables = ", ".join(sorted(model_tables - set(existing_schema)))
        raise RuntimeError(f"数据库只存在部分业务表，缺少：{missing_tables}")

    # 迁移完成后再检查一次，避免只改 Model 却忘记生成迁移文件。
    migrated_schema = await get_existing_schema()
    missing_tables, missing_columns = get_missing_structure(migrated_schema)
    if missing_tables or missing_columns:
        table_details = ", ".join(sorted(missing_tables)) or "无"
        column_details = "; ".join(
            f"{table}: {', '.join(sorted(columns))}"
            for table, columns in sorted(missing_columns.items())
        ) or "无"
        raise RuntimeError(
            "Model 与数据库结构不一致，请先生成 Alembic 迁移。"
            f"缺少表：{table_details}；缺少字段：{column_details}"
        )

import os
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


# 项目根目录，用于定位 env 和 alembic.ini 等项目级文件。
BASE_DIR = Path(__file__).resolve().parents[2]
# 优先读取系统环境变量 ENVIRONMENT；没有设置时默认使用开发环境 dev。
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")
# 根据环境名称选择配置文件，例如 dev 对应 env/.env.dev。
ENV_FILE = BASE_DIR / "env" / f".env.{ENVIRONMENT}"


class Settings(BaseSettings):
    """集中管理应用、跨域、数据库和登录配置。"""

    # 指定 Pydantic Settings 如何加载和检查环境配置。
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,  # 从上面计算出的环境配置文件读取值。
        env_file_encoding="utf-8",  # 按 UTF-8 读取中文等内容。
        extra="ignore",  # 配置文件出现暂未声明的字段时忽略它。
        case_sensitive=True,  # 配置名区分大小写，统一使用大写名称。
    )

    # 当前运行环境名称；未在 .env.dev 中配置时使用 dev。
    ENVIRONMENT: str = "dev"
    # 是否开启 FastAPI 调试模式；生产环境建议设置为 False。
    DEBUG: bool = True

    # FastAPI 应用名称，会显示在 /docs 和 OpenAPI 文档中。
    APP_TITLE: str = "新闻管理系统"
    # 当前应用版本号，会显示在 OpenAPI 文档中。
    APP_VERSION: str = "1.0.0"
    # 业务接口统一前缀，必须以 / 开头且末尾不能带 /。
    API_PREFIX: str = "/api"

    # 允许访问后端的前端地址；多个地址使用英文逗号分隔。
    CORS_ORIGINS: str = "*"
    # 允许的 HTTP 方法；* 表示允许全部方法。
    CORS_METHODS: str = "*"
    # 允许浏览器发送的请求头；* 表示允许全部请求头。
    CORS_HEADERS: str = "*"
    # 是否允许跨域请求携带 Cookie、Authorization 等凭证。
    ALLOW_CREDENTIALS: bool = True

    # MySQL 服务地址；数据库运行在本机时使用 localhost。
    DATABASE_HOST: str = "localhost"
    # MySQL 服务端口，默认端口是 3306。
    DATABASE_PORT: int = 3306
    # 登录 MySQL 使用的用户名。
    DATABASE_USER: str = "root"
    # 登录 MySQL 使用的密码；真实值只写在 .env.dev 中。
    DATABASE_PASSWORD: str = ""
    # 项目使用的数据库名称；不存在时初始化模块会自动创建。
    DATABASE_NAME: str = "news_app"
    # 是否在控制台输出 SQL，开发调试可开启，生产环境建议关闭。
    DATABASE_ECHO: bool = True
    # 连接池中长期保留的数据库连接数量。
    DATABASE_POOL_SIZE: int = 10
    # 连接池繁忙时允许临时增加的最大连接数量。
    DATABASE_MAX_OVERFLOW: int = 20
    # 是否在 FastAPI 启动时自动执行 Alembic 数据库迁移。
    DATABASE_AUTO_MIGRATE: bool = True

    # 用户登录令牌的有效天数。
    TOKEN_EXPIRE_DAYS: int = 7

    @staticmethod
    def _split_csv(value: str) -> list[str]:
        """把逗号分隔的配置转换成 Starlette 需要的字符串列表。"""
        return [item.strip() for item in value.split(",") if item.strip()]

    @property
    def ALLOW_ORIGINS(self) -> list[str]:
        """返回跨域中允许访问后端的前端地址列表。"""
        return self._split_csv(self.CORS_ORIGINS)

    @property
    def ALLOW_METHODS(self) -> list[str]:
        """返回跨域中允许使用的 HTTP 方法列表。"""
        return self._split_csv(self.CORS_METHODS)

    @property
    def ALLOW_HEADERS(self) -> list[str]:
        """返回跨域中允许浏览器发送的请求头列表。"""
        return self._split_csv(self.CORS_HEADERS)

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """拼接业务接口和 Alembic 使用的异步数据库连接地址。"""
        # 业务接口和 Alembic 使用这个地址连接指定数据库。
        username = quote_plus(self.DATABASE_USER)
        password = quote_plus(self.DATABASE_PASSWORD)
        return (
            f"mysql+aiomysql://{username}:{password}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}"
            f"/{self.DATABASE_NAME}?charset=utf8mb4"
        )

    @property
    def ASYNC_DATABASE_SERVER_URL(self) -> str:
        """连接 MySQL 服务，但暂不指定数据库。"""
        # 首次启动时数据库还不存在，因此这里不能在地址中填写数据库名。
        username = quote_plus(self.DATABASE_USER)
        password = quote_plus(self.DATABASE_PASSWORD)
        return (
            f"mysql+aiomysql://{username}:{password}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/?charset=utf8mb4"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """读取一次配置并在项目中复用。"""
    return Settings()


# 创建全局配置对象，其他模块导入 settings 即可读取相同配置。
settings = get_settings()

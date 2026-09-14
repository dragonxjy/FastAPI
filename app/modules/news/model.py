from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base


class Category(Base):
    # 跟数据库名对上
    __tablename__ = "news_category"
    # 给数据库表添加中文说明，方便在数据库工具中查看用途。
    __table_args__ = {"comment": "新闻分类表"}

    # autoincrement 自增
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="分类ID",
    )
    # unique=True、nullable=False：不允许重复，不允许为空
    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        comment="分类名称",
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="排序顺序",
    )

    # 方便调试
    def __repr__(self) -> str:
        return f"<Category id={self.id}, name={self.name}, sort_order={self.sort_order}>"


class News(Base):
    __tablename__ = "news"

    # 创建索引：提升查询速度
    __table_args__ = (
        Index("fk_news_category_idx", "category_id"),  # 高频查询场景
        Index("idx_publish_time", "publish_time"),  # 按照发布时间排序
        {"comment": "新闻表"},  # 数据库中的表说明
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="新闻ID",
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="新闻标题",
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="新闻简介",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="新闻内容",
    )
    image: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="封面图片URL",
    )
    author: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="作者",
    )
    category_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "news_category.id",
            name="fk_news_category",  # 固定外键名称，方便迁移时识别
            onupdate="CASCADE",  # 分类编号更新时同步更新新闻
            ondelete="RESTRICT",  # 分类仍有新闻时不允许删除
        ),
        nullable=False,
        comment="分类ID",
    )
    views: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="浏览量",
    )
    publish_time: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        comment="发布时间",
    )

    # 方便调试
    def __repr__(self) -> str:
        return f"<News id={self.id}, title={self.title!r}, views={self.views}>"

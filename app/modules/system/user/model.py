from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, Index, Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base


class User(Base):
    __tablename__ = "user"
    __table_args__ = (
        Index("username_UNIQUE", "username", unique=True),
        Index("phone_UNIQUE", "phone", unique=True),
        {"comment": "用户信息表"},  # 数据库中的表说明
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="用户ID",
    )
    username: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="用户名",
    )
    password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="密码（加密存储）",
    )
    nickname: Mapped[Optional[str]] = mapped_column(String(50), comment="昵称")
    avatar: Mapped[Optional[str]] = mapped_column(String(255), comment="头像URL",
                                                  default='https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg')
    gender: Mapped[Optional[str]] = mapped_column(
        Enum("male", "female", "unknown"),
        default="unknown",
        comment="性别",
    )
    bio: Mapped[Optional[str]] = mapped_column(String(500), comment="个人简介", default='这个⼈很懒，什么都没留下')
    phone: Mapped[Optional[str]] = mapped_column(String(20), comment="手机号")
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        comment="更新时间",
    )

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', nickname='{self.nickname}') > "


class UserToken(Base):
    __tablename__ = 'user_token'
    updated_at = None
    # 创建索引
    __table_args__ = (
        Index('fk_user_token_user_idx', 'user_id'),
        {"comment": "用户令牌表"},  # 数据库中的表说明
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="令牌ID")
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            User.id,
            name="fk_user_token_user",  # 固定外键名称，方便迁移时识别
            onupdate="CASCADE",  # 用户编号更新时同步更新令牌记录
            ondelete="CASCADE",  # 删除用户时同步删除其令牌
        ),
        nullable=False,
        comment="用户ID",
    )
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, comment="令牌值")
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="过期时间")
    # 传入 datetime.now 函数，新增数据时才会生成当前时间。
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")

    def _repr__(self):
        return f"<UserToken(id={self.id}, user_id={self.user_id}, token='{
        self.token}')>"

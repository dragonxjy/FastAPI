"""create initial tables

Revision ID: 74f0eea3ae76
Revises: 
Create Date: 2026-09-10 15:13:49.855747

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '74f0eea3ae76'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """首次部署时创建项目需要的四张业务表。"""
    # 先创建分类表，因为新闻表的 category_id 需要引用它。
    op.create_table('news_category',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='分类ID'),
    sa.Column('name', sa.String(length=50), nullable=False, comment='分类名称'),
    sa.Column('sort_order', sa.Integer(), nullable=False, comment='排序顺序'),
    sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
    sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name'),
    comment='新闻分类表'
    )

    # 创建用户表，并为用户名和手机号添加唯一索引。
    op.create_table('user',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='用户ID'),
    sa.Column('username', sa.String(length=50), nullable=False, comment='用户名'),
    sa.Column('password', sa.String(length=255), nullable=False, comment='密码（加密存储）'),
    sa.Column('nickname', sa.String(length=50), nullable=True, comment='昵称'),
    sa.Column('avatar', sa.String(length=255), nullable=True, comment='头像URL'),
    sa.Column('gender', sa.Enum('male', 'female', 'unknown'), nullable=True, comment='性别'),
    sa.Column('bio', sa.String(length=500), nullable=True, comment='个人简介'),
    sa.Column('phone', sa.String(length=20), nullable=True, comment='手机号'),
    sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
    sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
    sa.PrimaryKeyConstraint('id'),
    comment='用户信息表'
    )
    op.create_index('phone_UNIQUE', 'user', ['phone'], unique=True)
    op.create_index('username_UNIQUE', 'user', ['username'], unique=True)

    # 分类表已经存在，现在可以安全创建带分类外键的新闻表。
    op.create_table('news',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='新闻ID'),
    sa.Column('title', sa.String(length=255), nullable=False, comment='新闻标题'),
    sa.Column('description', sa.String(length=500), nullable=True, comment='新闻简介'),
    sa.Column('content', sa.Text(), nullable=False, comment='新闻内容'),
    sa.Column('image', sa.String(length=255), nullable=True, comment='封面图片URL'),
    sa.Column('author', sa.String(length=50), nullable=True, comment='作者'),
    sa.Column('category_id', sa.Integer(), nullable=False, comment='分类ID'),
    sa.Column('views', sa.Integer(), nullable=False, comment='浏览量'),
    sa.Column('publish_time', sa.DateTime(), nullable=False, comment='发布时间'),
    sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
    sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
    sa.ForeignKeyConstraint(
        ['category_id'],
        ['news_category.id'],
        name='fk_news_category',
        onupdate='CASCADE',
        ondelete='RESTRICT',
    ),
    sa.PrimaryKeyConstraint('id'),
    comment='新闻表'
    )
    op.create_index('fk_news_category_idx', 'news', ['category_id'], unique=False)
    op.create_index('idx_publish_time', 'news', ['publish_time'], unique=False)

    # 用户表已经存在，最后创建保存登录令牌的表。
    op.create_table('user_token',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='令牌ID'),
    sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
    sa.Column('token', sa.String(length=255), nullable=False, comment='令牌值'),
    sa.Column('expires_at', sa.DateTime(), nullable=False, comment='过期时间'),
    sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
    sa.ForeignKeyConstraint(
        ['user_id'],
        ['user.id'],
        name='fk_user_token_user',
        onupdate='CASCADE',
        ondelete='CASCADE',
    ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('token'),
    comment='用户令牌表'
    )
    op.create_index('fk_user_token_user_idx', 'user_token', ['user_id'], unique=False)


def downgrade() -> None:
    """回退首次迁移，按外键依赖的相反顺序删除表。"""
    # 先删除依赖其他表的新闻表和令牌表，避免外键阻止删除。
    op.drop_index('fk_user_token_user_idx', table_name='user_token')
    op.drop_table('user_token')
    op.drop_index('idx_publish_time', table_name='news')
    op.drop_index('fk_news_category_idx', table_name='news')
    op.drop_table('news')
    op.drop_index('username_UNIQUE', table_name='user')
    op.drop_index('phone_UNIQUE', table_name='user')
    op.drop_table('user')
    op.drop_table('news_category')

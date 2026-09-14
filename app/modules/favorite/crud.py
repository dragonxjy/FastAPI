from sqlalchemy import func, select, update, insert, delete
from sqlalchemy.ext.asyncio import AsyncSession

from .model import Favorite
from ..news.model import News


async def check_favorite_api(db: AsyncSession, user_id: int, news_id: int) -> bool:
    """检测新闻是否被用户收藏。"""
    statement = select(Favorite).where(
        Favorite.user_id == user_id,
        Favorite.news_id == news_id,
    )
    result = await db.execute(statement)
    return result.scalar_one_or_none() is not None


# 添加收藏
async def add_favorite_api(db: AsyncSession, user_id: int, news_id: int):
    """添加收藏。"""
    favorite = Favorite(user_id=user_id, news_id=news_id)
    db.add(favorite)
    await db.commit()
    await db.refresh(favorite)
    return favorite


async def cancel_favorite_api(db: AsyncSession, user_id: int, news_id: int):
    """取消收藏。"""
    statement = delete(Favorite).where(
        Favorite.user_id == user_id,
        Favorite.news_id == news_id,
    )
    result = await db.execute(statement)
    await db.commit()
    return result.rowcount > 0


# 获取收藏列表：获取的是某个用户的收藏列表 + 分页功能
async def get_favorite_list_api(
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 10
):
    # 总量 + 收藏的新闻列表
    count_query = select(func.count()).where(Favorite.user_id == user_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    # 获取收藏列表 - 联表查询 join() + 收藏时间排序 + 分页
    # select(查询主体模型类, 字段别名).join(联合查询的模型类, 联合查询的条件).where().order_by().offset().limit()
    # 别名： Favorite.created_at.label("favorite_time")
    offset = (page - 1) * page_size
    # [
    #   (新闻对象, 收藏时间, 收藏id)
    # ]
    query = (select(News, Favorite.created_at.label("favorite_time"), Favorite.id.label("favorite_id"))
             .join(Favorite, Favorite.news_id == News.id)
             .where(Favorite.user_id == user_id)
             .order_by(Favorite.created_at.desc())
             .offset(offset).limit(page_size)
             )
    result = await db.execute(query)
    rows = result.all()
    return rows, total


# 清空
async def clear_favorite_list_api(db: AsyncSession, user_id: int):
    """清空收藏列表。"""
    statement = delete(Favorite).where(Favorite.user_id == user_id)
    result = await db.execute(statement)
    await db.commit()
    return result.rowcount or 0

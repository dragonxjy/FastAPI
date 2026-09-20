from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .model import Category, News


# 获取分类列表
async def get_categories_api(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 100,
) -> list[Category]:
    """
    获取分类列表
    :param db: 数据库会话
    :param page: 页码
    :param page_size: 每页数量
    :return: 分类列表
    """
    # 每次直接读取数据库；固定排序后再分页，保证不同页的数据稳定。
    skip = (page - 1) * page_size
    statement = select(Category).order_by(Category.sort_order, Category.id).offset(skip).limit(page_size)
    result = await db.execute(statement)
    categories = list(result.scalars().all())
    return categories


async def get_news_list_api(
        db: AsyncSession,
        category_id: int,
        page: int,
        page_size: int,
) -> list[News]:
    """
    获取新闻列表
    :param db: 数据库会话
    :param category_id: 分类 ID
    :param page: 页码
    :param page_size: 每页数量
    :return: 新闻列表
    """
    # 列表直接读取数据库，因此新增、修改或删除后，下次查询就能看到结果。
    stmt = (
        select(News).where(News.category_id == category_id)
        .order_by(News.publish_time.desc(), News.id.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )
    result = await db.execute(stmt)
    news_list = result.scalars().all()

    return news_list


# 获取新闻总数
async def get_news_count_api(db: AsyncSession, category_id: int) -> int:
    """
    获取新闻总数
    :param db: 数据库会话
    :param category_id: 分类 ID
    :return: 新闻总数
    """
    statement = (
        select(func.count(News.id))
        .where(News.category_id == category_id)
    )
    result = await db.execute(statement)
    return result.scalar_one()  # 只能有一个结果，否则报错


# 获取新闻详情
async def get_news_detail_api(db: AsyncSession, news_id: int) -> News | None:
    """
    获取新闻详情
    :param db: 数据库会话
    :param news_id: 新闻 ID
    :return: 新闻详情或 None
    """
    return await db.get(News, news_id)  # 有就返回，没有就返回 None


# 新闻浏览量
async def update_news_view_count_api(db: AsyncSession, news_id: int) -> bool:
    """
    新闻浏览量
    :param db: 数据库会话
    :param news_id: 新闻 ID
    :return: 是否更新成功
    """
    # 如果数据库没有命中怎么办
    statement = (
        update(News)
        .where(News.id == news_id)
        .values(views=News.views + 1)
    )
    result = await db.execute(statement)
    # 更新后检查数据库是否真的命中了数据，命中了返回 True
    return result.rowcount > 0


# 获取同类推荐新闻
async def get_related_news_api(
        db: AsyncSession,
        news_id: int,
        category_id: int,
        page_size: int = 10,
) -> list[News]:
    """
    获取同类推荐新闻
    :param db: 数据库会话
    :param news_id: 当前新闻 ID
    :param category_id: 分类 ID
    :param page_size: 返回数量
    :return: 同类新闻列表
    """
    statement = (
        select(News)
        .where(
            News.category_id == category_id,
            News.id != news_id,
        )
        .order_by(News.publish_time.desc())
        .limit(page_size)
    )
    result = await db.execute(statement)
    # 原代码通过列表推导式整理新闻核心数据，现在由 Schema 统一筛选响应字段
    return list(result.scalars().all())

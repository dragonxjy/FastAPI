from sqlalchemy.ext.asyncio import AsyncSession

from . import crud as news_db
from .model import Category


class NewsViewUpdateError(Exception):
    """新闻存在，但浏览量更新没有命中数据。"""
    pass


async def get_categories_service(
    db: AsyncSession,
    page: int,
    page_size: int,
) -> list[Category]:
    """获取分页分类列表。"""
    return await news_db.get_categories_api(db, page, page_size)


async def get_news_list_service(
    db: AsyncSession,
    category_id: int,
    page: int,
    page_size: int,
) -> dict[str, object]:
    """组合新闻列表、总数和后续加载状态。"""
    news_list = await news_db.get_news_list_api(
        db,
        category_id,
        page,
        page_size,
    )
    total = await news_db.get_news_count_api(db, category_id)
    skip = (page - 1) * page_size

    return {
        "total": total,
        "data": news_list,
        "has_more": skip + len(news_list) < total,
    }


async def get_news_detail_service(
    db: AsyncSession,
    news_id: int,
) -> dict[str, object] | None:
    """组合新闻详情、浏览量更新和同类推荐。"""
    # 1.查询新闻详情
    news_detail = await news_db.get_news_detail_api(db, news_id)
    if news_detail is None:
        return None

    # 2.更新浏览量
    updated = await news_db.update_news_view_count_api(db, news_id)
    if not updated:
        raise NewsViewUpdateError

    # 3.查询同类推荐新闻
    related_news = await news_db.get_related_news_api(
        db,
        news_id,
        news_detail.category_id,
    )

    return {
        **vars(news_detail),
        "related_news": related_news,
    }

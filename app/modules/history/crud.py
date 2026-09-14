from datetime import datetime

from sqlalchemy import func, select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.history.model import History
from app.modules.news.model import News


async def add_history_view_api(db: AsyncSession, user_id: int, news_id: int):
    """
    添加历史记录
    """
    query = select(History).where(History.user_id == user_id, History.news_id == news_id)
    result = await db.execute(query)
    existing_history = result.scalar_one_or_none()
    if existing_history:
        existing_history.view_time = datetime.now()
        await db.commit()
        await db.refresh(existing_history)
        return existing_history
    else:
        history = History(user_id=user_id, news_id=news_id)
        db.add(history)
        await db.commit()
        await db.refresh(history)
        return history


# 获取浏览历史：联表查询新闻信息 + 按浏览时间倒序 + 分页
async def get_history_view_api(db: AsyncSession, user_id: int, page: int, page_size: int):
    offset = (page - 1) * page_size
    count_query = select(func.count(History.id)).where(History.user_id == user_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    query = (select(News, History.view_time.label("view_time"), History.id.label("history_id"))
             .join(History, History.news_id == News.id)
             .where(History.user_id == user_id)
             .order_by(History.view_time.desc())
             .offset(offset).limit(page_size))

    result = await db.execute(query)
    rows = result.all()
    return rows, total


async def remove_history_view_api(db, user_id, news_id):
    statement = delete(History).where(news_id == History.news_id, user_id == History.user_id)
    result = await db.execute(statement)
    await db.commit()
    return result.rowcount > 0


async def clear_history_view_api(db: AsyncSession, user_id: int):
    statement = delete(History).where(History.user_id == user_id)
    result = await db.execute(statement)
    await db.commit()
    return result.rowcount or 0

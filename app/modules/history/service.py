from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from . import crud as history_db
from .schema import HistoryRequest, HistoryListResponse


async def add_history_view_service(db: AsyncSession, user_id: int, news_id: int):
    return await history_db.add_history_view_api(db, user_id, news_id)


async def get_history_view_service(db: AsyncSession, user_id: int, page: int, page_size: int):
    rows, total = await history_db.get_history_view_api(db, user_id, page, page_size)
    # 组装：新闻字段 + 浏览历史字段（view_time/history_id）
    history_list = [{
        **news.__dict__,
        "view_time": view_time,
        "history_id": history_id,
    } for news, view_time, history_id in rows]
    has_more = total > page * page_size

    return HistoryListResponse(list=history_list, total=total, has_more=has_more)



async def remove_history_view_service(db: AsyncSession, user_id: int, news_id: int):
    result = await history_db.remove_history_view_api(db, user_id, news_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="历史记录不存在")
    return result


async def clear_history_view_service(db: AsyncSession, user_id: int):
    return await history_db.clear_history_view_api(db, user_id)

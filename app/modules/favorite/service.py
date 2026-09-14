from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from . import crud as favorite_db
from .model import Favorite
from .schema import FavoriteListResponse


async def check_favorite_service(db: AsyncSession, user_id: int, news_id: int):
    return await favorite_db.check_favorite_api(db, user_id, news_id)


# 添加收藏
async def add_favorite_service(db: AsyncSession, user_id: int, news_id: int):
    return await favorite_db.add_favorite_api(db, user_id, news_id)


# 取消收藏
async def cancel_favorite_service(db: AsyncSession, user_id: int, news_id: int):
    result = await favorite_db.cancel_favorite_api(db, user_id, news_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_405_NOT_FOUND, detail="记录不存在")
    return result


# 获取收藏列表
async def get_favorite_list_service(db: AsyncSession, user_id: int, page: int, page_size: int):
    rows, total = await favorite_db.get_favorite_list_api(db, user_id, page, page_size)
    favorite_list = [{
        **news.__dict__,
        "favorite_time": favorite_time,
        "favorite_id": favorite_id
    } for news, favorite_time, favorite_id in rows]
    has_more = total > page * page_size

    data = FavoriteListResponse(list=favorite_list, total=total, hasMore=has_more)
    return data


# 清空收藏列表
async def clear_favorite_list_service(db: AsyncSession, user_id: int):
    result = await favorite_db.clear_favorite_list_api(db, user_id)
    return result



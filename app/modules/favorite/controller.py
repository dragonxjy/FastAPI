from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.common.response import Success_response
from app.core.database import get_database
from . import service as news_service
from .schema import FavoriteCheckResponse, FavoriteAddRequest

from ..system.user.model import User
from ...utils.auth import get_current_user

# 创建 APIRouter 实例
# prefix 路由前缀（API 接口规范文档）
# tags 分组标签
FavoriteRouter = APIRouter(prefix="/favorite", tags=["收藏模块"])


# 检测新闻收藏状态
@FavoriteRouter.get(
    "/check",
    summary="检测新闻收藏状态",
)
async def check_favorite(
        news_id: int = Query(..., alias="newsId", gt=0),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database)
):
    result = await news_service.check_favorite_service(db, user.id, news_id)

    return Success_response(data=FavoriteCheckResponse(isFavorite=result))


# 添加收藏
@FavoriteRouter.post(
    "/add",
    summary="添加收藏",
)
async def add_favorite(
        data: FavoriteAddRequest,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database)
):
    await news_service.add_favorite_service(db, user.id, data.news_id)
    return Success_response(message="添加收藏成功")


# 取消收藏
@FavoriteRouter.delete(
    "/remove",
    summary="取消收藏",
)
async def cancel_favorite(
        news_id: int = Query(..., alias="newsId"),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database)
):
    await news_service.cancel_favorite_service(db, user.id, news_id)
    return Success_response(message="取消收藏成功")


# 获取收藏列表
@FavoriteRouter.get(
    "/list",
    summary="获取收藏列表",
)
async def get_favorite_list(
        page: int = Query(..., gt=0, alias="page"),
        page_size: int = Query(..., gt=0, alias="pageSize"),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database)
):
    result = await news_service.get_favorite_list_service(db, user.id, page, page_size)
    # if not result:
    #     raise HTTPException(status_code=status.HTTP_405_NOT_FOUND, detail="收藏列表为空")
    return Success_response(data=result)


# 清空收藏列表
@FavoriteRouter.delete(
    "/clear",
    summary="清空收藏列表",
)
async def clear_favorite_list(
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database)
):
    total = await news_service.clear_favorite_list_service(db, user.id)
    return Success_response(message=f"成功清除{total}条数据")

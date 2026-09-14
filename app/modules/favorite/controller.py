from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import Success_response
from app.common.schema import MessageResponse, error_response
from app.core.database import get_database
from . import service as news_service
from .schema import (
    FavoriteAddRequest,
    FavoriteCheckApiResponse,
    FavoriteCheckResponse,
    FavoriteListApiResponse,
)

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
    description="检查当前登录用户是否已经收藏指定新闻。",
    response_model=FavoriteCheckApiResponse,
    response_description="返回指定新闻的收藏状态。",
    operation_id="checkFavoriteStatus",
    responses={
        401: error_response("token 缺失、无效或已过期。", "无效的令牌或已经过期的令牌", 401),
        500: error_response("数据库或服务器异常。", "数据库操作失败，请稍后重试", 500),
    },
)
async def check_favorite(
    news_id: int = Query(
        ...,
        alias="newsId",
        gt=0,
        description="需要检查的新闻 ID。",
        examples=[1],
    ),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    result = await news_service.check_favorite_service(db, user.id, news_id)

    return Success_response(data=FavoriteCheckResponse(isFavorite=result))


# 添加收藏
@FavoriteRouter.post(
    "/add",
    summary="添加收藏",
    description="将指定新闻加入当前登录用户的收藏列表。同一用户不能重复收藏同一条新闻。",
    response_model=MessageResponse,
    response_description="收藏添加成功。",
    operation_id="addFavorite",
    responses={
        400: error_response("新闻不存在或该新闻已经收藏。", "数据约束冲突，请检查输入", 400),
        401: error_response("token 缺失、无效或已过期。", "无效的令牌或已经过期的令牌", 401),
        500: error_response("数据库或服务器异常。", "数据库操作失败，请稍后重试", 500),
    },
)
async def add_favorite(
    data: FavoriteAddRequest = Body(..., description="需要收藏的新闻。"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    await news_service.add_favorite_service(db, user.id, data.news_id)
    return Success_response(message="添加收藏成功")


# 取消收藏
@FavoriteRouter.delete(
    "/remove",
    summary="取消收藏",
    description="从当前登录用户的收藏列表中删除指定新闻。",
    response_model=MessageResponse,
    response_description="收藏取消成功。",
    operation_id="removeFavorite",
    responses={
        401: error_response("token 缺失、无效或已过期。", "无效的令牌或已经过期的令牌", 401),
        404: error_response("收藏记录不存在。", "记录不存在", 404),
        500: error_response("数据库或服务器异常。", "数据库操作失败，请稍后重试", 500),
    },
)
async def cancel_favorite(
    news_id: int = Query(
        ...,
        alias="newsId",
        gt=0,
        description="需要取消收藏的新闻 ID。",
        examples=[1],
    ),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    await news_service.cancel_favorite_service(db, user.id, news_id)
    return Success_response(message="取消收藏成功")


# 获取收藏列表
@FavoriteRouter.get(
    "/list",
    summary="获取收藏列表",
    description="按收藏时间倒序分页返回当前登录用户收藏的新闻。",
    response_model=FavoriteListApiResponse,
    response_description="收藏列表获取成功。",
    operation_id="getFavoriteList",
    responses={
        401: error_response("token 缺失、无效或已过期。", "无效的令牌或已经过期的令牌", 401),
        500: error_response("数据库或服务器异常。", "数据库操作失败，请稍后重试", 500),
    },
)
async def get_favorite_list(
    page: int = Query(..., gt=0, description="页码，从 1 开始。", examples=[1]),
    page_size: int = Query(
        ...,
        gt=0,
        le=100,
        alias="pageSize",
        description="每页收藏数量，最大 100。",
        examples=[10],
    ),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    result = await news_service.get_favorite_list_service(db, user.id, page, page_size)
    # if not result:
    #     raise HTTPException(status_code=status.HTTP_405_NOT_FOUND, detail="收藏列表为空")
    return Success_response(data=result)


# 清空收藏列表
@FavoriteRouter.delete(
    "/clear",
    summary="清空收藏列表",
    description="删除当前登录用户的全部收藏记录，不会删除新闻本身。",
    response_model=MessageResponse,
    response_description="收藏列表清空成功，message 中包含删除数量。",
    operation_id="clearFavoriteList",
    responses={
        401: error_response("token 缺失、无效或已过期。", "无效的令牌或已经过期的令牌", 401),
        500: error_response("数据库或服务器异常。", "数据库操作失败，请稍后重试", 500),
    },
)
async def clear_favorite_list(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    total = await news_service.clear_favorite_list_service(db, user.id)
    return Success_response(message=f"成功清除{total}条数据")

from fastapi import APIRouter, Body, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import Success_response
from app.common.schema import BooleanResponse, CountResponse, error_response
from app.core.database import get_database
from . import service as history_service
from .schema import HistoryListApiResponse, HistoryRecordApiResponse, HistoryRequest
from ..system.user.model import User
from ...utils.auth import get_current_user

# 创建 APIRouter 实例
# prefix 路由前缀（API 接口规范文档）
# tags 分组标签
HistoryRouter = APIRouter(prefix="/history", tags=["浏览历史模块"])


# 添加历史预览
@HistoryRouter.post(
    "/add",
    summary="添加或更新浏览历史",
    description=(
        "记录当前用户浏览过的新闻。如果该新闻已经存在于浏览历史中，"
        "不会重复创建记录，而是把浏览时间更新为当前时间。"
    ),
    response_model=HistoryRecordApiResponse,
    response_description="返回新增或更新后的浏览历史记录。",
    operation_id="addHistoryRecord",
    responses={
        400: error_response("指定新闻不存在或数据约束冲突。", "关联数据不存在", 400),
        401: error_response("token 缺失、无效或已过期。", "无效的令牌或已经过期的令牌", 401),
        500: error_response("数据库或服务器异常。", "数据库操作失败，请稍后重试", 500),
    },
)
async def add_history_view(
    data: HistoryRequest = Body(..., description="本次浏览的新闻。"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    result = await history_service.add_history_view_service(db, user.id, data.news_id)
    return Success_response(data=result)


# 获取历史预览
@HistoryRouter.get(
    "/list",
    summary="获取浏览历史",
    description="按最近浏览时间倒序分页返回当前登录用户的浏览历史。",
    response_model=HistoryListApiResponse,
    response_description="浏览历史列表获取成功。",
    operation_id="getHistoryList",
    responses={
        401: error_response("token 缺失、无效或已过期。", "无效的令牌或已经过期的令牌", 401),
        500: error_response("数据库或服务器异常。", "数据库操作失败，请稍后重试", 500),
    },
)
async def get_history_view(
    page: int = Query(..., gt=0, description="页码，从 1 开始。", examples=[1]),
    page_size: int = Query(
        ...,
        gt=0,
        le=100,
        alias="pageSize",
        description="每页历史记录数量，最大 100。",
        examples=[10],
    ),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    result = await history_service.get_history_view_service(db, user.id, page, page_size)
    return Success_response(data=result)

# 删除单条历史记录
@HistoryRouter.delete(
    "/delete/{news_id}",
    summary="删除一条浏览历史",
    description="根据新闻 ID 删除当前登录用户的一条浏览历史。",
    response_model=BooleanResponse,
    response_description="删除成功时 data 为 true。",
    operation_id="deleteHistoryRecord",
    responses={
        401: error_response("token 缺失、无效或已过期。", "无效的令牌或已经过期的令牌", 401),
        404: error_response("对应的浏览历史不存在。", "历史记录不存在", 404),
        500: error_response("数据库或服务器异常。", "数据库操作失败，请稍后重试", 500),
    },
)
async def remove_history_view(
    news_id: int = Path(..., gt=0, description="需要删除历史记录的新闻 ID。", examples=[1]),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    result = await history_service.remove_history_view_service(db, user.id, news_id)
    return Success_response(data=result)


# 清空浏览历史
@HistoryRouter.delete(
    "/clear",
    summary="清空浏览历史",
    description="删除当前登录用户的全部浏览历史，不会删除新闻本身。",
    response_model=CountResponse,
    response_description="data 为本次删除的历史记录数量。",
    operation_id="clearHistoryList",
    responses={
        401: error_response("token 缺失、无效或已过期。", "无效的令牌或已经过期的令牌", 401),
        500: error_response("数据库或服务器异常。", "数据库操作失败，请稍后重试", 500),
    },
)
async def clear_history_view(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    result = await history_service.clear_history_view_service(db, user.id)
    return Success_response(data=result)

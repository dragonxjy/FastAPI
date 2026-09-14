from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_database
from . import service as history_service
from .schema import HistoryRequest
from ..system.user.model import User
from app.common.response import Success_response
from ...utils.auth import get_current_user

# 创建 APIRouter 实例
# prefix 路由前缀（API 接口规范文档）
# tags 分组标签
HistoryRouter = APIRouter(prefix="/history", tags=["浏览历史模块"])


# 添加历史预览
@HistoryRouter.post("/add")
async def add_history_view(
        data: HistoryRequest,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database)
):
    result = await history_service.add_history_view_service(db, user.id, data.news_id)
    return Success_response(data=result)


# 获取历史预览
@HistoryRouter.get("/list")
async def get_history_view(
        page: int = Query(..., gt=0, alias="page"),
        page_size: int = Query(..., gt=0, alias="pageSize"),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database)
):
    result = await history_service.get_history_view_service(db, user.id, page, page_size)
    return Success_response(data=result)

# s删除当条历史记录
@HistoryRouter.delete("/delete/{news_id}")

async def remove_history_view(
        news_id: int,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database)
):
    result = await history_service.remove_history_view_service(db, user.id, news_id)
    return Success_response(data=result)


# 清空浏览历史
@HistoryRouter.delete("/clear")

async def clear_history_view(
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database)
):
    result = await history_service.clear_history_view_service(db, user.id)
    return Success_response(data=result)

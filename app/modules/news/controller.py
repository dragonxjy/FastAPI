from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import Success_response
from app.core.database import get_database

from .schema import (
    CategoryListResponse,
    NewsDetailResponse,
    NewsListResponse,
)
from . import service as news_service
from .service import NewsViewUpdateError

# 创建 APIRouter 实例
# prefix 路由前缀（API 接口规范文档）
# tags 分组标签
NewsRouter = APIRouter(prefix="/news", tags=["新闻模块"])


# 接口实现流程
# 1.模块化路由 → API 接口规范文档
# 2.定义模型类 → 数据库表（数据库设计文档）
# 3.在 db 文件夹中封装操作数据库的方法
# 4.在 services 文件夹中组合业务流程
# 5.在路由处理函数中调用 service 方法并响应结果
@NewsRouter.get(
    "/categories",
    summary="获取分类列表",
    response_model=CategoryListResponse,
)
async def get_category_list(
        page: int = Query(1, ge=1),
        page_size: int = Query(100, alias="pageSize", ge=1, le=100),
        db: AsyncSession = Depends(get_database),
):
    # 先获取数据库中的新闻分类数据 → 定义模型类 → 封装查询数据的方法
    categories = await news_service.get_categories_service(db, page, page_size)
    return Success_response(message="获取分类成功", data=categories)


@NewsRouter.get(
    "/list",
    summary="获取新闻列表",
    response_model=NewsListResponse,
)
async def get_news_list(
        category_id: int = Query(..., alias="categoryId", gt=0),
        page: int = Query(1, ge=1),
        page_size: int = Query(10, alias="pageSize", ge=1, le=100),
        db: AsyncSession = Depends(get_database),
):
    # 思路：处理分页规则 → 查询新闻列表 → 计算总量 → 计算是否还有更多
    result = await news_service.get_news_list_service(
        db,
        category_id,
        page,
        page_size,
    )

    return Success_response(
        message="获取新闻列表成功",
        data=result["data"],
        total=result["total"],
        has_more=result["has_more"],
    )


# 获取新闻详情
@NewsRouter.get(
    "/detail",
    summary="获取新闻详情",
    response_model=NewsDetailResponse,
)
async def get_news_detail(
        news_id: int = Query(..., alias="newsId", gt=0),
        db: AsyncSession = Depends(get_database),
):
    try:
        # Service 负责查询详情、更新浏览量和查询同类新闻
        data = await news_service.get_news_detail_service(db, news_id)
    except NewsViewUpdateError as exc:
        raise HTTPException(
            status_code=500,
            detail="更新浏览量失败",
        ) from exc

    if data is None:
        raise HTTPException(status_code=404, detail="新闻不存在")

    return Success_response(message="获取新闻详情成功", data=data)

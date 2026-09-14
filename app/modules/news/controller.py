from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import Success_response
from app.common.schema import error_response
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
    description=(
        "分页获取新闻分类，结果按数据库中的分类顺序返回。"
        "客户端通常在首页加载时调用该接口生成分类标签。"
    ),
    response_model=CategoryListResponse,
    response_description="分类列表获取成功。",
    operation_id="getNewsCategories",
    responses={
        500: error_response("数据库或服务器异常。", "数据库操作失败，请稍后重试", 500),
    },
)
async def get_category_list(
    page: int = Query(1, ge=1, description="页码，从 1 开始。", examples=[1]),
    page_size: int = Query(
        100,
        alias="pageSize",
        ge=1,
        le=100,
        description="每页分类数量，范围为 1 至 100。",
        examples=[20],
    ),
    db: AsyncSession = Depends(get_database),
):
    # 先获取数据库中的新闻分类数据 → 定义模型类 → 封装查询数据的方法
    categories = await news_service.get_categories_service(db, page, page_size)
    return Success_response(message="获取分类成功", data=categories)


@NewsRouter.get(
    "/list",
    summary="获取新闻列表",
    description=(
        "按分类分页查询新闻。响应同时返回该分类的新闻总数，以及是否还有下一页。"
        "列表项包含正文，客户端可以按需展示摘要或跳转详情。"
    ),
    response_model=NewsListResponse,
    response_description="新闻列表获取成功。",
    operation_id="getNewsList",
    responses={
        500: error_response("数据库或服务器异常。", "数据库操作失败，请稍后重试", 500),
    },
)
async def get_news_list(
    category_id: int = Query(
        ...,
        alias="categoryId",
        gt=0,
        description="需要查询的新闻分类 ID。",
        examples=[1],
    ),
    page: int = Query(1, ge=1, description="页码，从 1 开始。", examples=[1]),
    page_size: int = Query(
        10,
        alias="pageSize",
        ge=1,
        le=100,
        description="每页新闻数量，范围为 1 至 100。",
        examples=[10],
    ),
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
    description=(
        "根据新闻 ID 查询完整内容。查询成功后浏览量增加 1，"
        "并返回最多 10 条相同分类的推荐新闻。"
    ),
    response_model=NewsDetailResponse,
    response_description="新闻详情获取成功。",
    operation_id="getNewsDetail",
    responses={
        404: error_response("指定新闻不存在。", "新闻不存在", 404),
        500: error_response("浏览量更新或数据库操作失败。", "更新浏览量失败", 500),
    },
)
async def get_news_detail(
    news_id: int = Query(
        ...,
        alias="newsId",
        gt=0,
        description="需要查看的新闻 ID。",
        examples=[1],
    ),
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

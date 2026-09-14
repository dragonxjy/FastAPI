
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.common.schema import ApiResponse
from app.modules.favorite.base import NewsItemBase


class FavoriteCheckResponse(BaseModel):
    is_favorite: bool = Field(
        ...,
        alias="isFavorite",
        description="当前用户是否已收藏指定新闻。",
        examples=[True],
    )

    model_config = ConfigDict(populate_by_name=True)


class FavoriteAddRequest(BaseModel):
    news_id: int = Field(
        ...,
        gt=0,
        alias="newsId",
        description="需要收藏的新闻 ID。",
        examples=[1],
    )

    model_config = ConfigDict(populate_by_name=True)


# 规划两个类： 一个是新闻模型类 + 收藏的模型类
class FavoriteNewsItemResponse(NewsItemBase):
    favorite_id: int = Field(alias="favoriteId", description="收藏记录 ID。", examples=[12])
    favorite_time: datetime = Field(alias="favoriteTime", description="收藏时间。")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )
# 收藏列表接口响应模型类
class FavoriteListResponse(BaseModel):
    items: list[FavoriteNewsItemResponse] = Field(alias="list", description="当前页收藏新闻列表。")
    total: int = Field(description="收藏记录总数。", examples=[12])
    has_more: bool = Field(alias="hasMore", description="是否还有下一页。", examples=[False])

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )


class FavoriteCheckApiResponse(ApiResponse[FavoriteCheckResponse]):
    """收藏状态响应。"""


class FavoriteListApiResponse(ApiResponse[FavoriteListResponse]):
    """收藏列表响应。"""

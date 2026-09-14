from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from app.common.schema import ApiResponse
from app.modules.favorite.base import NewsItemBase


class HistoryRequest(BaseModel):
    news_id: int = Field(
        ...,
        gt=0,
        alias="newsId",
        description="本次浏览的新闻 ID。重复添加时会更新浏览时间。",
        examples=[1],
    )

    model_config = ConfigDict(populate_by_name=True)


class HistoryRecordResponse(BaseModel):
    id: int = Field(description="浏览历史记录 ID。", examples=[24])
    user_id: int = Field(description="当前用户 ID。", examples=[1])
    news_id: int = Field(description="新闻 ID。", examples=[1])
    view_time: datetime = Field(description="最近一次浏览时间。")

    model_config = ConfigDict(from_attributes=True)


class HistoryNewsItemResponse(NewsItemBase):
    """
    浏览历史列表中的新闻项响应
    """
    history_id: int = Field(alias="historyId", description="浏览历史记录 ID。")
    view_time: datetime = Field(alias="viewTime", description="最近一次浏览时间。")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True)


class HistoryListResponse(BaseModel):
    items: list[HistoryNewsItemResponse] = Field(alias="list", description="当前页浏览历史列表。")
    total: int = Field(description="浏览历史总数。", examples=[20])
    has_more: bool = Field(alias="hasMore", description="是否还有下一页。", examples=[True])

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )


class HistoryRecordApiResponse(ApiResponse[HistoryRecordResponse]):
    """新增或更新时间后的浏览历史响应。"""


class HistoryListApiResponse(ApiResponse[HistoryListResponse]):
    """浏览历史列表响应。"""

from datetime import datetime

from pydantic import Field, BaseModel, ConfigDict
from typing import Optional


class NewsItemBase(BaseModel):
    id: int = Field(description="新闻 ID。", examples=[1])
    title: str = Field(description="新闻标题。", examples=["新闻标题示例"])
    description: Optional[str] = Field(None, description="新闻摘要。")
    image: Optional[str] = Field(None, description="新闻封面图片 URL。")
    author: Optional[str] = Field(None, description="新闻作者或来源。")
    category_id: int = Field(description="所属新闻分类 ID。", alias="categoryId", examples=[1])
    views: int = Field(description="累计浏览次数。", examples=[12581])
    publish_time: Optional[datetime] = Field(
        None,
        alias="publishedTime",
        description="新闻发布时间。",
        examples=["2024-01-01T08:00:00"],
    )

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApiSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class CategoryRead(ApiSchema):
    id: int = Field(description="新闻分类 ID。", examples=[1])
    name: str = Field(description="新闻分类名称。", examples=["头条"])
    sort_order: int = Field(description="分类显示顺序，数值越小越靠前。", examples=[1])


class NewsRead(ApiSchema):
    id: int = Field(description="新闻 ID。", examples=[1])
    title: str = Field(description="新闻标题。", examples=["新闻标题示例"])
    description: str | None = Field(
        description="新闻摘要。",
        examples=["这是一段新闻摘要。"],
    )
    content: str = Field(description="新闻正文。", examples=["新闻正文内容。"])
    image: str | None = Field(
        description="新闻封面图片 URL。",
        examples=["https://picsum.photos/id/100/200/200"],
    )
    author: str | None = Field(description="新闻作者或来源。", examples=["新华社"])
    category_id: int = Field(description="所属新闻分类 ID。", examples=[1])
    views: int = Field(description="累计浏览次数。", examples=[12581])
    publish_time: datetime = Field(
        description="新闻发布时间，格式为 ISO 8601。",
        examples=["2024-01-01T08:00:00"],
    )


class RelatedNewsRead(ApiSchema):
    id: int = Field(description="推荐新闻 ID。", examples=[2])
    title: str = Field(description="推荐新闻标题。", examples=["同类新闻标题"])
    image: str | None = Field(description="推荐新闻封面图片 URL。")
    author: str | None = Field(description="推荐新闻作者或来源。")
    publish_time: datetime = Field(description="推荐新闻发布时间。")
    category_id: int = Field(description="推荐新闻所属分类 ID。", examples=[1])
    views: int = Field(description="推荐新闻浏览次数。", examples=[8924])


class NewsDetailRead(NewsRead):
    related_news: list[RelatedNewsRead] = Field(description="最多 10 条同分类推荐新闻。")


class CategoryListResponse(ApiSchema):
    message: str = Field(description="请求结果说明。", examples=["获取分类成功"])
    code: int = Field(200, description="业务状态码。", examples=[200])
    data: list[CategoryRead] = Field(description="分页后的新闻分类列表。")


class NewsListResponse(ApiSchema):
    message: str = Field(description="请求结果说明。", examples=["获取新闻列表成功"])
    code: int = Field(200, description="业务状态码。", examples=[200])
    total: int = Field(description="当前分类下的新闻总数。", examples=[50])
    data: list[NewsRead] = Field(description="当前页新闻数据。")
    has_more: bool = Field(description="是否还有下一页数据。", examples=[True])


class NewsDetailResponse(ApiSchema):
    message: str = Field(description="请求结果说明。", examples=["获取新闻详情成功"])
    code: int = Field(200, description="业务状态码。", examples=[200])
    data: NewsDetailRead = Field(description="新闻详情及同类推荐。")

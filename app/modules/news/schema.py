from datetime import datetime

from pydantic import BaseModel, ConfigDict


def to_camel(field_name: str) -> str:
    """将 Python 的下划线字段名转换为接口使用的驼峰命名。"""
    first, *rest = field_name.split("_")
    return first + "".join(word.capitalize() for word in rest)


class ApiSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=to_camel,
    )


class CategoryRead(ApiSchema):
    id: int
    name: str
    sort_order: int


class NewsRead(ApiSchema):
    id: int
    title: str
    description: str | None
    content: str
    image: str | None
    author: str | None
    category_id: int
    views: int
    publish_time: datetime


class RelatedNewsRead(ApiSchema):
    id: int
    title: str
    image: str | None
    author: str | None
    publish_time: datetime
    category_id: int
    views: int


class NewsDetailRead(NewsRead):
    related_news: list[RelatedNewsRead]


class CategoryListResponse(ApiSchema):
    message: str
    code: int
    data: list[CategoryRead]


class NewsListResponse(ApiSchema):
    message: str
    code: int
    total: int
    data: list[NewsRead]
    has_more: bool


class NewsDetailResponse(ApiSchema):
    message: str
    code: int
    data: NewsDetailRead

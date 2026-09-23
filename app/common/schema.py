from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


DataT = TypeVar("DataT")


class ApiResponse(BaseModel, Generic[DataT]):
    """统一的成功响应结构。"""

    code: int = Field(
        200,
        description="业务状态码；成功时固定为 200。",
        examples=[200],
    )
    message: str = Field(
        description="本次操作的结果说明。",
        examples=["操作成功"],
    )
    data: DataT = Field(description="接口返回的业务数据。")

    model_config = ConfigDict(populate_by_name=True)


class MessageResponse(BaseModel):
    """不需要返回业务数据的成功响应。"""

    code: int = Field(200, description="业务状态码。", examples=[200])
    message: str = Field(description="操作结果说明。", examples=["操作成功"])
    data: None = Field(None, description="该接口没有额外业务数据。")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"code": 200, "message": "操作成功", "data": None},
            ]
        }
    )


class BooleanResponse(ApiResponse[bool]):
    """业务结果为布尔值的成功响应。"""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"code": 200, "message": "success", "data": True},
            ]
        }
    )


class CountResponse(ApiResponse[int]):
    """业务结果为受影响记录数的成功响应。"""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"code": 200, "message": "success", "data": 3},
            ]
        }
    )


class ErrorResponse(BaseModel):
    """项目全局异常处理器返回的错误结构。"""

    code: int = Field(description="HTTP 状态码。", examples=[400])
    message: str = Field(
        description="可供客户端展示或排查问题的错误信息。",
        examples=["请求参数错误"],
    )
    data: Any | None = Field(
        None,
        description="错误详情；生产环境通常为 null。",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"code": 400, "message": "请求参数错误", "data": None},
            ]
        }
    )


def error_response(description: str, message: str, code: int) -> dict[str, Any]:
    """生成供路由 responses 参数复用的错误响应文档。"""
    return {
        "model": ErrorResponse,
        "description": description,
        "content": {
            "application/json": {
                "example": {"code": code, "message": message, "data": None}
            }
        },
    }

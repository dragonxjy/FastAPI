
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.common.schema import ApiResponse

# 注册参数
class RegisterUser(BaseModel):
    username: str = Field(
        description="登录用户名；在系统中必须唯一。",
        examples=["demo_user"],
    )
    password: str = Field(
        description="登录密码；后端会进行哈希存储，请通过 HTTPS 传输。",
        examples=["demo123456"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"username": "demo_user", "password": "demo123456"}]
        }
    )


# 登录参数
class LoginUser(BaseModel):
    username: str = Field(description="已注册的用户名。", examples=["demo_user"])
    password: str = Field(description="用户密码。", examples=["demo123456"])
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [{"username": "demo_user", "password": "demo123456"}]
        },
    )


# user_info 对应的类：基础类 + Info 类（id、用户名）
class UserInfoBase(BaseModel):
    """
    用户信息基础数据模型
    """
    nickname: Optional[str] = Field(None, max_length=50, description="用户昵称。", examples=["小明"])
    avatar: Optional[str] = Field(
        None,
        max_length=255,
        description="头像图片 URL。",
        examples=["https://example.com/avatar.png"],
    )
    gender: Optional[Literal["male", "female", "unknown"]] = Field(
        None,
        description="性别：male 男、female 女、unknown 未设置。",
        examples=["unknown"],
    )
    bio: Optional[str] = Field(
        None,
        max_length=500,
        description="个人简介。",
        examples=["热爱阅读和科技。"],
    )


class UserInfoResponse(UserInfoBase):
    id: int = Field(description="用户 ID。", examples=[1])
    username: str = Field(description="登录用户名。", examples=["demo_user"])

    # 模型类配置
    model_config = ConfigDict(
        from_attributes=True  # 允许从 ORM 对象属性中取值
    )





# data 数据类型
class UserAuthResponse(BaseModel):
    token: str = Field(
        description="登录令牌；后续请求放入 Authorization 请求头。",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    user_info: UserInfoResponse = Field(..., alias="userInfo", description="当前用户公开资料。")

    # 模型类配置
    model_config = ConfigDict(
        populate_by_name=True,  # alias / 字段名兼容
        from_attributes=True  # 允许从 ORM 对象属性中取值
    )


# 更新用户信息的模型类
class UserUpdateRequest(BaseModel):
    nickname: Optional[str] = Field(None, max_length=50, description="新昵称。", examples=["小明"])
    avatar: Optional[str] = Field(None, max_length=255, description="新头像图片 URL。")
    gender: Optional[Literal["male", "female", "unknown"]] = Field(
        None,
        description="新性别设置。",
        examples=["unknown"],
    )
    bio: Optional[str] = Field(None, max_length=500, description="新的个人简介。")
    phone: Optional[str] = Field(None, max_length=20, description="手机号；非空值必须唯一。")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "nickname": "小明",
                    "avatar": "https://example.com/avatar.png",
                    "gender": "unknown",
                    "bio": "热爱阅读和科技。",
                    "phone": "13800138000",
                }
            ]
        }
    )


class UserChangePasswordRequest(BaseModel):
    old_password: str = Field(
        ...,
        alias="oldPassword",
        description="当前登录密码。",
        examples=["demo123456"],
    )
    new_password: str = Field(
        ...,
        min_length=6,
        alias="newPassword",
        description="新密码，至少 6 个字符。",
        examples=["newPassword123"],
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {"oldPassword": "demo123456", "newPassword": "newPassword123"}
            ]
        },
    )


class UserAuthApiResponse(ApiResponse[UserAuthResponse]):
    """注册或登录成功响应。"""


class UserInfoApiResponse(ApiResponse[UserInfoResponse]):
    """用户资料响应。"""


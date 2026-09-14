from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import Success_response
from app.common.schema import MessageResponse, error_response
from app.core.database import get_database
from app.utils.auth import get_current_user
from .model import User
from .schema import (
    LoginUser,
    RegisterUser,
    UserAuthResponse,
    UserChangePasswordRequest,
    UserAuthApiResponse,
    UserInfoResponse,
    UserInfoApiResponse,
    UserUpdateRequest,
)
from .service import (
    change_password_service,
    get_login_service,
    get_register_service,
    get_user_info_service,
    update_user_service,
)

UserRouter = APIRouter(prefix="/user", tags=["用户模块"])


@UserRouter.post(
    "/register",
    summary="注册用户",
    description=(
        "使用唯一用户名和密码创建账号。密码会经过哈希处理后保存；"
        "注册成功后同时签发登录 token，无需再次登录。"
    ),
    response_model=UserAuthApiResponse,
    response_description="注册成功，返回 token 和用户公开资料。",
    operation_id="registerUser",
    responses={
        400: error_response("用户名已存在或数据约束冲突。", "用户已存在", 400),
        500: error_response("数据库或服务器异常。", "数据库操作失败，请稍后重试", 500),
    },
)
async def register(
    users: RegisterUser = Body(..., description="新用户的登录凭据。"),
    db: AsyncSession = Depends(get_database),
):
    user, token = await get_register_service(users, db)
    response_data = UserAuthResponse(
        token=token,
        user_info=UserInfoResponse.model_validate(user),
    )
    return Success_response(message="注册成功", data=response_data)


# 登录
@UserRouter.post(
    "/login",
    summary="用户登录",
    description=(
        "校验用户名和密码并签发新的 token。每个用户只保留一个有效 token，"
        "重复登录会使此前签发的 token 失效。"
    ),
    response_model=UserAuthApiResponse,
    response_description="登录成功，返回 token 和用户公开资料。",
    operation_id="loginUser",
    responses={
        401: error_response("用户名不存在或密码错误。", "用户名或密码错误", 401),
        500: error_response("数据库或服务器异常。", "数据库操作失败，请稍后重试", 500),
    },
)
async def login(
    users: LoginUser = Body(..., description="已注册用户的登录凭据。"),
    db: AsyncSession = Depends(get_database),
):
    user, token = await get_login_service(users, db)
    response_data = UserAuthResponse(
        token=token,
        user_info=UserInfoResponse.model_validate(user),
    )
    return Success_response(message="登录成功", data=response_data)


# 获取用户信息
@UserRouter.get(
    "/info",
    summary="获取当前用户资料",
    description="根据 Authorization 请求头中的 token 返回当前登录用户的公开资料。",
    response_model=UserInfoApiResponse,
    response_description="用户资料获取成功。",
    operation_id="getCurrentUserInfo",
    responses={
        401: error_response("token 缺失、无效或已过期。", "无效的令牌或已经过期的令牌", 401),
        500: error_response("数据库或服务器异常。", "数据库操作失败，请稍后重试", 500),
    },
)
async def info(user: User = Depends(get_current_user)):
    # 控制层只接收请求，用户信息交给 Service 层统一整理。
    user_info = await get_user_info_service(user)
    return Success_response(message="获取用户信息成功", data=user_info)


# 更新用户信息
@UserRouter.put(
    "/update",
    summary="更新当前用户资料",
    description=(
        "部分更新当前登录用户的昵称、头像、性别、简介或手机号。"
        "请求体中未传递或值为 null 的字段不会修改。"
    ),
    response_model=UserInfoApiResponse,
    response_description="资料更新成功，返回更新后的用户资料。",
    operation_id="updateCurrentUser",
    responses={
        400: error_response("没有可更新字段、手机号重复或数据约束冲突。", "没有需要更新的字段", 400),
        401: error_response("token 缺失、无效或已过期。", "无效的令牌或已经过期的令牌", 401),
        404: error_response("当前用户不存在。", "用户不存在", 404),
        500: error_response("数据库或服务器异常。", "数据库操作失败，请稍后重试", 500),
    },
)
async def update(
    user_data: UserUpdateRequest = Body(..., description="需要更新的用户资料字段。"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    # Service 负责业务判断，再调用 CRUD 更新数据库。
    updated_user = await update_user_service(db, user, user_data)
    return Success_response(
        message="更新用户信息成功",
        data=UserInfoResponse.model_validate(updated_user),
    )


# 更新密码
@UserRouter.put(
    "/password",
    summary="修改当前用户密码",
    description=(
        "验证旧密码后设置新密码。新密码至少 6 个字符，保存前会进行哈希处理。"
    ),
    response_model=MessageResponse,
    response_description="密码修改成功。",
    operation_id="changeCurrentUserPassword",
    responses={
        400: error_response("旧密码错误。", "旧密码错误", 400),
        401: error_response("token 缺失、无效或已过期。", "无效的令牌或已经过期的令牌", 401),
        500: error_response("数据库或服务器异常。", "数据库操作失败，请稍后重试", 500),
    },
)
async def update_password(
    password_data: UserChangePasswordRequest = Body(..., description="旧密码和新密码。"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    # 旧密码校验和修改结果判断都由 Service 层处理。
    await change_password_service(db, user, password_data)
    return Success_response(message="更新密码成功")

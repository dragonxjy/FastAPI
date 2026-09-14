from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.utils.password_util import verify_password

from . import crud as users
from .model import User
from .schema import (
    LoginUser,
    RegisterUser,
    UserChangePasswordRequest,
    UserInfoResponse,
    UserUpdateRequest,
)


# 用户注册
async def get_register_service(users_data: RegisterUser, db: AsyncSession):
    # 注册前先查询用户名，避免重复创建同名用户。
    existing_user = await users.get_user_by_username_api(db, users_data.username)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户已存在")

    # 用户创建成功后生成 Token，注册完成即可保持登录状态。
    user = await users.create_user_api(db, users_data)
    token = await users.create_token_api(db, user.id)
    return user, token


# 用户登录
async def get_login_service(users_data: LoginUser, db: AsyncSession):
    # 查询用户是否存在。
    user = await users.get_user_by_username_api(db, users_data.username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    # 明文密码必须通过密码工具与数据库中的哈希值进行验证。
    if not verify_password(users_data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    # 登录成功后生成新 Token，并使旧 Token 失效。
    token = await users.create_token_api(db, user.id)
    return user, token


# 根据 Token 获取当前用户
async def get_user_by_token_service(db: AsyncSession, token: str) -> User:
    # Service 调用 CRUD 查询数据库，不让鉴权工具越过 Service 直接访问 CRUD。
    user = await users.get_user_by_token_api(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌或已经过期的令牌",
        )
    return user


# 获取用户信息
async def get_user_info_service(user: User) -> UserInfoResponse:
    # 只返回响应模型声明的安全字段，避免把密码等内部字段返回给客户端。
    return UserInfoResponse.model_validate(user)


# 更新用户信息
async def update_user_service(
    db: AsyncSession,
    user: User,
    user_data: UserUpdateRequest,
) -> User:
    # 当前用户已经通过 Token 验证，使用其用户名定位要更新的数据。
    return await users.update_user_api(db, user.username, user_data)


# 修改密码
async def change_password_service(
    db: AsyncSession,
    user: User,
    password_data: UserChangePasswordRequest,
) -> None:
    # CRUD 返回 False 表示旧密码校验失败，Service 负责转换成业务异常。
    updated = await users.change_password_api(
        db,
        user,
        password_data.old_password,
        password_data.new_password,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误",
        )

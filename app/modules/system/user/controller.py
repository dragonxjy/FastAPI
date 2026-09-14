from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import Success_response
from app.core.database import get_database
from app.utils.auth import get_current_user
from .model import User
from .schema import (
    LoginUser,
    RegisterUser,
    UserAuthResponse,
    UserChangePasswordRequest,
    UserInfoResponse,
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


@UserRouter.post("/register")
async def register(users: RegisterUser, db: AsyncSession = Depends(get_database)):  # 用户信息 和 db
    user, token = await get_register_service(users, db)
    response_data = UserAuthResponse(
        token=token,
        user_info=UserInfoResponse.model_validate(user),
    )
    return Success_response(message="注册成功", data=response_data)


# 登录
@UserRouter.post("/login")
async def login(users: LoginUser, db: AsyncSession = Depends(get_database)):
    user, token = await get_login_service(users, db)
    response_data = UserAuthResponse(
        token=token,
        user_info=UserInfoResponse.model_validate(user),
    )
    return Success_response(message="登录成功", data=response_data)


# 获取用户信息
@UserRouter.get("/info")
async def info(user: User = Depends(get_current_user)):
    # 控制层只接收请求，用户信息交给 Service 层统一整理。
    user_info = await get_user_info_service(user)
    return Success_response(message="获取用户信息成功", data=user_info)


# 更新用户信息
@UserRouter.put("/update")
async def update(
    user_data: UserUpdateRequest,
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
@UserRouter.put("/password")
async def update_password(
    password_data: UserChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    # 旧密码校验和修改结果判断都由 Service 层处理。
    await change_password_service(db, user, password_data)
    return Success_response(message="更新密码成功")

from datetime import datetime, timedelta

import uuid

from fastapi import HTTPException, security
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.utils.password_util import get_password_hash, verify_password

from .model import User, UserToken
from .schema import RegisterUser, UserUpdateRequest


# 根据用户名查询数据库
async def get_user_by_username_api(db: AsyncSession, username: str):
    query = select(User).where(User.username == username)
    result = await db.execute(query)
    return result.scalar_one_or_none()


# 创建用户
async def create_user_api(db: AsyncSession, user_data: RegisterUser):
    # 先密码加密处理 → add
    hashed_password = get_password_hash(user_data.password)
    user = User(username=user_data.username, password=hashed_password)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def create_token_api(db: AsyncSession, user_id: int):
    # 生成 Token +设置过期时间 →查询数据库当前用户是否有 Token →有:更新；没有:添加
    token = str(uuid.uuid4())
    # timedelta(days=7, hours=2, minutes=30, seconds=10)
    expires_at = datetime.now() + timedelta(days=settings.TOKEN_EXPIRE_DAYS)
    query = select(UserToken).where(UserToken.user_id == user_id)
    result = await db.execute(query)
    user_token = result.scalar_one_or_none()
    if user_token:
        user_token.token = token
        user_token.expires_at = expires_at
    else:
        user_token = UserToken(user_id=user_id, token=token, expires_at=expires_at)
        db.add(user_token)
        await db.commit()
    return token


# 根据 Token 查询用户:验证 Token → 查询
async def get_user_by_token_api(db: AsyncSession, token: str):
    query = select(UserToken).where(UserToken.token == token)
    result = await db.execute(query)
    db_token = result.scalar_one_or_none()
    if not db_token or db_token.expires_at < datetime.now():
        return None
    query = select(User).where(User.id == db_token.user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


# 更新用户信息：update更新→检查是否命中→获取更新后的用户返回
async def update_user_api(db: AsyncSession, username: str, user_data: UserUpdateRequest):
    # update(User).where(User.username == username).values(字段=值,字段=值)
    # user_data 是一个Pydantic类型，得到字典→ **解包
    # 没有设置值的不更新
    update_data = user_data.model_dump(
        exclude_unset=True,
        exclude_none=True
    )
    # id 仅用于定位，不允许通过请求体修改主键
    update_data.pop("id", None)
    if not update_data:
        raise HTTPException(status_code=400, detail="没有需要更新的字段")
    query = update(User).where(User.username == username).values(**update_data)
    result = await db.execute(query)
    await db.commit()
    # 检查更新
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="用户不存在")
    # 获取一下更新后的用户
    updated_user = await get_user_by_username_api(db, username)
    return updated_user


# 修改密码：验证旧密码新密码加密→修改密码
async def change_password_api(db: AsyncSession, user: User, old_password: str, new_password: str):
    if not verify_password(old_password, user.password):
        return False
    hashed_new_pwd = get_password_hash(new_password)
    user.password = hashed_new_pwd
    # 更新：由SQLAlchemy真正接管这个 User 对象，确保可以 commit
    # 规避session 过期或关闭导致的不能提交的问题
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return True

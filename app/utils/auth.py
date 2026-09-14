from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_database
from app.modules.system.user import service as users


authorization_header = APIKeyHeader(
    name="Authorization",
    scheme_name="BearerAuth",
    description=(
        "登录接口返回的 token。推荐格式：`Bearer <token>`；"
        "为兼容现有客户端，也可以直接填写 token。"
    ),
    auto_error=False,
)


async def get_current_user(
    authorization: Annotated[str | None, Security(authorization_header)],
    db: AsyncSession = Depends(get_database),
):
    """校验 Authorization 请求头并返回当前登录用户。"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少登录令牌",
        )
    value = authorization.strip()
    token = value[7:].strip() if value.lower().startswith("bearer ") else value
    return await users.get_user_by_token_service(db, token)

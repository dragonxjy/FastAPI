"""v1 路由总表。"""

from fastapi import APIRouter

from app.core.config import settings
from app.modules.news.controller import NewsRouter
from app.modules.system.user.controller import UserRouter
from app.modules.favorite.controller import FavoriteRouter
from app.modules.history.controller import HistoryRouter
from app.modules.agent.controller import AgentRouter


api_v1 = APIRouter(prefix=settings.API_PREFIX)
api_v1.include_router(NewsRouter)
api_v1.include_router(UserRouter)
api_v1.include_router(FavoriteRouter)
api_v1.include_router(HistoryRouter)
api_v1.include_router(AgentRouter)



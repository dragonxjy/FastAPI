"""HTTP 接口只管收消息和校验登录，Agent 逻辑放在 service.py。"""

from fastapi import APIRouter, Depends

from app.common.response import Success_response
from app.modules.agent.service import ChatRequest, LLM_MODEL, model_configured, run_chat
from app.modules.system.user.model import User
from app.utils.auth import get_current_user


AgentRouter = APIRouter(prefix="/agent", tags=["文章 AI 助手"])


@AgentRouter.get("/status", summary="查看模型是否配置")
async def agent_status():
    # 只返回布尔状态和模型名，永远不返回 API Key。
    return Success_response(data={"configured": model_configured(), "model": LLM_MODEL})


@AgentRouter.post("/chat", summary="通过自然语言管理文章")
async def chat(body: ChatRequest, user: User = Depends(get_current_user)):
    # 即使工具是真实写数据库，也必须先通过现有账号的登录校验。
    return Success_response(data=await run_chat(body))

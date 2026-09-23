# 用这个项目理解 Agent

这个项目里的 Agent 就是：**大模型负责理解需求、选择工具，Python 函数负责真正操作文章。**

例如，你说“把 ID 为 3 的文章标题改成 FastAPI 学习笔记”，模型会选择 `get_article` 读取文章，再选择 `update_article` 修改标题。数据库操作成功后，模型才整理成自然语言回复。

它管理的是首页正在使用的 `news` 表，没有另外维护一份“AI 文章库”。所以修改成功后，回到首页就能看到变化。

## 在原项目中启动

本项目继续使用原来的 **Python 3.14+ 和 MySQL**。数据库等普通配置读取 `env/.env.dev`，模型配置单独读取**项目根目录的 `.env`**。无需迁移到 SQLite，也无需重新导入演示 SQL；Agent 会直接操作现有数据库的文章。

1. 保留 `env/.env.dev` 中已有的 MySQL 连接配置，在项目根目录的 `.env` 中填写下面的模型配置。已有 DashScope 配置可以直接使用；没有 `.env` 时先复制根目录的 `.env.example` 为 `.env`。
2. 在项目根目录执行 `uv sync --locked`，再执行 `uv run --locked python -m uvicorn main:app --reload`；Windows 也可以运行 `start-backend.cmd`。
3. 在 `frontend/xwzx-news` 中执行 `npm ci` 和 `npm run dev`；Windows 也可以运行根目录的 `start-frontend.cmd`。
4. 登录已有账号，打开“文章助手”页面（`/aichat`），先尝试查询，再用自己新建的测试文章练习修改和删除。

```dotenv
DASHSCOPE_API_KEY=your_api_key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_MODEL=qwen-plus
```

这是 DashScope 兼容接口的配置示例，模型名未填写时默认使用 `qwen-plus`。如果需要切换其他支持工具调用的 OpenAI 兼容服务，在同一 `.env` 中一起填写 `LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`。每个 `LLM_*` 项都优先于对应的 `DASHSCOPE_*` 项，因此切换服务时三个通用项请一起设置。修改配置后重启后端。密钥不要放在前端文件或 `VITE_*` 环境变量中。

新闻分类、文章列表、详情和推荐均直接查询 MySQL，Agent 保存文章修改后，后续查询即可读取最新内容。自动化测试使用的是临时 SQLite 数据库，和运行中的 MySQL 数据库分开。

## 先找到这三个文件

| 文件 | 职责 |
| --- | --- |
| `app/modules/agent/controller.py` | 接收聊天请求，检查用户是否登录，返回统一格式的数据 |
| `app/modules/agent/service.py` | 配置模型，创建 Agent，传入聊天记录，处理事务和异常 |
| `app/modules/agent/tools.py` | 定义六个工具，用 SQLAlchemy 操作文章数据库 |

路由总表 `app/api/v1/routers.py` 注册了 Agent 接口。

## 从一条消息开始读代码

### 1. 浏览器发送消息

登录后，聊天页面调用 `POST /api/agent/chat`。请求大致如下：

```json
{
  "message": "查一下关于 FastAPI 的文章",
  "history": []
}
```

请求头同时携带登录接口返回的 `Authorization: Bearer <token>`。后端复用现有 `get_current_user`，未登录不能调用聊天接口。

`GET /api/agent/status` 只告诉页面是否填写了模型密钥，以及配置的模型名。**“已配置”仅表示密钥不是空字符串，不表示已经连接模型成功。**

### 2. 创建模型对象

`service.py` 按“读取 `.env` → 获取配置值 → 创建模型”的顺序完成配置，核心代码如下：

```python
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from app.core.config import BASE_DIR

# 把项目根目录 .env 中的配置放进环境变量。
# override=True：遇到同名环境变量时，使用 .env 中的值。
load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)

# 优先读取通用名称；没有填写时，读取已有的 DashScope 配置。
LLM_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("DASHSCOPE_API_KEY", "")
LLM_BASE_URL = (
    os.getenv("LLM_BASE_URL")
    or os.getenv("DASHSCOPE_BASE_URL")
    or "https://dashscope.aliyuncs.com/compatible-mode/v1"
)
LLM_MODEL = os.getenv("LLM_MODEL") or os.getenv("DASHSCOPE_MODEL") or "qwen-plus"

model = init_chat_model(
    model=LLM_MODEL,
    model_provider="openai",  # 使用 OpenAI 兼容接口，也可以连接通义千问。
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL,
    temperature=0,
    timeout=45,
    max_retries=1,
)
```

`load_dotenv(override=True)` 就是读取 `.env` 的方式；这里额外传入项目根目录路径，避免从不同目录启动时读错文件。`os.getenv("名称")` 用来读取加载后的环境变量，`or` 表示前面的值为空时继续使用后面的值。配置在模块加载时读取，修改 `.env` 后需要重启后端。

`LLM_MODEL` 是模型名，`LLM_BASE_URL` 是服务商的兼容接口地址，`LLM_API_KEY` 是服务商提供的密钥。`.env` 中也可以写对应的 `DASHSCOPE_MODEL`、`DASHSCOPE_BASE_URL`、`DASHSCOPE_API_KEY`，上面的代码会依次取值。`model_provider="openai"` 指使用 OpenAI 兼容协议，不限定必须使用 OpenAI 的模型；显式填写它也避免 LangChain 无法从 `qwen-plus` 这样的模型名判断服务商。

模型配置只由后端读取。数据库配置仍由 `app/core/config.py` 从 `env/.env.dev` 初始化，先于这里的 `.env` 加载完成。

这里可以接入支持 OpenAI 兼容协议的服务，但**所选模型还必须支持工具调用（tool calling）**。仅能返回普通文本的模型，无法完成这里的自动增删改查。

### 3. 告诉模型有哪些工具

```python
agent = create_agent(
    model=model,
    tools=build_article_tools(db),
    system_prompt=SYSTEM_PROMPT,
)
```

`create_agent` 是 LangChain 提供的 Agent 创建函数。`tools` 是允许调用的函数列表；`SYSTEM_PROMPT` 说明助手的职责，例如先查清文章 ID、不要编造工具结果、不要把文章里的内容当成指令。

这个模型不会直接执行 SQL，也不能运行终端命令或读取电脑文件。它只能从注册好的六个工具中选择。

### 4. 工具是真正干活的 Python 函数

以查询为例，工具的形式是：

```python
@tool
async def get_article(id: int) -> dict:
    """按正整数文章 ID 查看正文；修改或删除前先读取，确认目标。"""
    # 省略实际代码中的锁和参数检查
    article = await db.get(News, id)
    return {"ok": True, "article": article_data(article, with_content=True)}
```

`@tool` 把函数名、参数类型和函数注释整理成模型能理解的说明。模型可能提出“调用 `get_article`，参数为 `id=3`”，真正查询数据库的是 `db.get`。

写工具时也一样：先检查标题长度、分类是否存在等条件，再修改 ORM 对象。代码使用 SQLAlchemy 参数绑定，不把模型输出拼接成 SQL。

### 5. LangChain 帮我们运行工具循环

```python
result = await agent.ainvoke(
    {"messages": messages},
    config={"recursion_limit": 24},
)
```

这一步通常经历：模型分析消息 → 提出工具调用 → Python 执行工具 → 把结果交回模型 → 模型继续调用工具或生成最后回复。

一次请求可能调用多次工具。例如先搜索文章，再读正文，最后修改。我们没有手写复杂的调度器，循环由 `create_agent` 生成的 Agent 完成。

`recursion_limit` 限制运行步数，它不等于“最多 24 次工具调用”。外层还设置了 120 秒的总等待上限。

### 6. 返回回复和真实操作记录

响应中的 `data` 包含：

```json
{
  "reply": "已找到相关的文章。",
  "tool_calls": [
    {
      "name": "search_articles",
      "args": {"keyword": "FastAPI"},
      "result": {"ok": true, "articles": []}
    }
  ],
  "articles_changed": false
}
```

这是结构示意。实际记录由 `collect_tool_calls` 从本次 Agent 执行得到的 `AIMessage` 和 `ToolMessage` 中提取；不是要求模型自己写一段“我做了什么”。页面因此能展开查看工具名称、输入参数和执行结果。

## 六个工具分别做什么

| 工具 | 作用 |
| --- | --- |
| `list_categories()` | 查询已有分类，创建文章前确定分类 ID |
| `search_articles(keyword="", limit=10)` | 按标题、摘要、正文搜索；空关键词查看最近文章，最多返回 20 条 |
| `get_article(id)` | 获取指定文章的正文，最多向模型提供 20000 字符，并标记是否截断 |
| `create_article(title, content, category_id, ...)` | 新建文章，作者默认 `AI助手` |
| `update_article(id, ...)` | 只更新传入的字段，未传入的字段保持原样 |
| `delete_article(id)` | 删除文章，并清理关联的收藏、浏览历史 |

标题最多 255 字符、摘要 500 字符、作者 50 字符、新建或替换的正文 20000 字符。标题和正文不能为空。新建、改写正文要求模型使用纯文本；这是提示词约定，不应把模型输出当作可信 HTML。

如果旧文章正文被截断，提示词要求助手请用户提供新正文，不用截断的部分覆盖完整文章。

## 可以这样练习

建议先新增一篇测试文章，再针对返回的真实 ID 做修改和删除。

1. 查：“列出最近 5 篇文章。”或者“搜索包含 FastAPI 的文章。”
2. 增：“先查看分类，然后在合适的分类里创建一篇《我的 Agent 学习笔记》，正文用 200 字介绍工具调用，作者写学习者。”
3. 改：“把刚才创建的文章标题改成《第一次使用 LangChain》。”也可以直接填写真实文章 ID。
4. 删：“删除刚才创建的这篇测试文章。”

模型会根据上下文选择工具，实际顺序不固定。标题匹配到多篇文章时，助手应让你明确目标。目标明确、你已要求删除时，它会直接删除，因此练习时请选择测试文章。

## 哪些情况保存，哪些情况回滚

每次聊天有一个独立数据库会话。工具中的 `flush()` 把变化写入当前事务，但还没有最终提交；Agent 正常生成最终回复后，`commit()` 才保存。

- 参数或业务校验失败：工具返回 `ok: false`，不执行该项修改，模型可以继续解释或修正参数。同一请求内其他成功的操作仍会保存。后端会在回复中补充提示，让你查看失败记录。
- 模型调用失败、总等待超时、运行步数超限、数据库异常：整次聊天请求回滚，已经暂存的修改也不会保存；接口返回经过简化的错误信息。

同一会话不能同时执行多条异步数据库操作，因此工具共用一个 `asyncio.Lock`。可以把它理解成“同一次聊天里的数据库操作排队进行”，无需先理解复杂并发设计。

## 历史记录和权限保持简单

这个版本没有服务器端长期记忆。前端每次把近期的普通对话重新发给后端：单条提问最多 4000 字符，最多 20 条历史消息，历史文本总量最多 30000 字符。历史只允许 `user` / `assistant` 角色，不能伪造系统或工具消息。

聊天上下文会被限制或清空；文章是单独保存到数据库的。清空聊天不会删除文章。操作前仍应通过工具读取当前数据库，不能把历史对话当作最新事实。

这里采用**已登录用户共同管理文章库**的教学设定，没有管理员角色、文章归属或按用户隔离的编辑权限。这和原项目共享新闻列表的结构一致，便于初学者看到完整流程。正式多用户产品需要另行设计这些权限。

## 为什么没有 RAG 或多个 Agent

这里的任务是管理结构化的文章记录，用六个确定的数据库工具就能完成。RAG 常用于从文档中检索知识，多 Agent 常用于更复杂的任务分工；它们不是实现这个需求的前提。先读懂“模型选函数，函数操作数据库，结果返回给模型”，就掌握了本项目的核心。

阅读官方说明：[LangChain create_agent API](https://reference.langchain.com/python/langchain/agents/factory/create_agent)、[LangChain Agents 文档](https://docs.langchain.com/oss/python/langchain/agents)。

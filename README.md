# 新闻资讯全栈应用Demo

一个面向移动端的前后端分离新闻应用。后端基于 FastAPI 提供异步 REST API，前端使用 Vue 3、Vant 和 Pinia，实现新闻浏览、分类筛选、用户登录、收藏、浏览历史、主题切换、中英文切换和流式 AI 问答等功能。

![Python](https://img.shields.io/badge/Python-3.14+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.141+-009688?logo=fastapi&logoColor=white)
![Vue](https://img.shields.io/badge/Vue-3-4FC08D?logo=vuedotjs&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0+-4479A1?logo=mysql&logoColor=white)

## 功能特性

- 新闻分类、分页列表、详情和同类新闻推荐
- 新闻浏览量统计
- 用户注册、登录、资料编辑和密码修改
- 新闻收藏、取消收藏、收藏列表和一键清空
- 浏览历史记录、单条删除和一键清空
- Pinia 状态管理及本地持久化
- 浅色、深色、蓝色、绿色四种主题
- 中文、英文界面切换
- 基于阿里云 DashScope 兼容接口的流式 AI 问答
- FastAPI 自动生成 Swagger 和 ReDoc 接口文档
- SQLAlchemy 异步访问 MySQL，支持 Alembic 自动迁移
- Redis 缓存不可用时自动回退到数据库查询

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 前端 | Vue 3、Vite 7、Vue Router、Pinia、Vant 4、Axios、Vue I18n |
| AI 展示 | DashScope OpenAI 兼容接口、SSE、Marked、DOMPurify |
| 后端 | Python 3.14、FastAPI、Uvicorn、Pydantic Settings |
| 数据访问 | SQLAlchemy 2 Async、aiomysql、Alembic |
| 数据存储 | MySQL 8、Redis（可选） |
| 包管理 | uv、npm |

## 系统架构

```mermaid
flowchart LR
    Browser[Vue 3 移动端] -->|REST API| API[FastAPI]
    Browser -->|SSE 流式请求| AI[DashScope API]
    API --> Router[Controller / Router]
    Router --> Service[Service]
    Service --> CRUD[CRUD]
    CRUD --> MySQL[(MySQL)]
    Service -. 可选缓存 .-> Redis[(Redis)]
```

后端按 `Controller -> Service -> CRUD -> Model` 分层。统一业务接口前缀为 `/api`，成功响应采用以下结构：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

## 项目结构

```text
.
├─ app/
│  ├─ api/v1/                 # API 路由汇总
│  ├─ cache/                  # 新闻缓存封装
│  ├─ common/                 # 统一响应结构
│  ├─ core/                   # 配置、数据库、Redis、异常处理
│  ├─ modules/
│  │  ├─ news/                # 新闻分类、列表和详情
│  │  ├─ favorite/            # 用户收藏
│  │  ├─ history/             # 浏览历史
│  │  └─ system/user/         # 注册、登录和用户资料
│  └─ utils/                  # 鉴权和密码工具
├─ alembic/                   # 数据库迁移
├─ env/.env.example           # 后端配置模板
├─ frontend/xwzx-news/        # Vue 前端项目
│  └─ src/
│     ├─ components/          # 公共组件
│     ├─ config/              # API 配置
│     ├─ i18n/                # 中英文文案
│     ├─ router/              # 前端路由
│     ├─ store/               # Pinia Store
│     └─ views/               # 页面组件
├─ static/news_app.sql        # 完整表结构和演示数据
├─ main.py                    # FastAPI 入口
├─ pyproject.toml             # Python 项目与依赖配置
└─ test_main.http             # 基础接口请求示例
```

## 快速开始

### 1. 环境要求

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)（推荐）
- Node.js `^20.19.0` 或 `>=22.12.0`
- MySQL 8.0+
- Redis（可选，默认地址为 `localhost:6379`）

### 2. 获取项目

```bash
git clone <your-repository-url>
cd fast-api-getting-started-demo-main
```

### 3. 配置后端

复制配置模板：

```powershell
# Windows PowerShell
Copy-Item env\.env.example env\.env.dev
```

```bash
# macOS / Linux / Git Bash
cp env/.env.example env/.env.dev
```

打开 `env/.env.dev`，至少填写本机 MySQL 密码：

```dotenv
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_USER=root
DATABASE_PASSWORD=your_database_password
DATABASE_NAME=news_app
DATABASE_AUTO_MIGRATE=true
```

项目通过 `ENVIRONMENT` 选择配置文件，默认值为 `dev`，对应 `env/.env.dev`。

### 4. 导入演示数据库

推荐导入 `static/news_app.sql`。该文件包含完整的 8 张表、8 个新闻分类和 400 余条演示新闻，可直接体验全部功能。

```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS news_app CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root -p news_app < static/news_app.sql
```

Windows PowerShell 可使用：

```powershell
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS news_app CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
Get-Content -Raw -Encoding UTF8 .\static\news_app.sql | mysql -u root -p news_app
```

> 直接启动一个空数据库时，Alembic 当前只会创建新闻分类、新闻、用户和令牌四张核心表。收藏与浏览历史依赖 SQL 文件中的表结构，因此体验完整功能时请先导入演示数据库。

### 5. 启动后端

```bash
uv sync --locked
uv run uvicorn main:app --reload
```

启动后可访问：

- 服务地址：<http://127.0.0.1:8000>
- Swagger：<http://127.0.0.1:8000/docs>
- ReDoc：<http://127.0.0.1:8000/redoc>

应用启动时会检查数据库结构，并在 `DATABASE_AUTO_MIGRATE=true` 时自动执行尚未应用的 Alembic 迁移。

### 6. 配置并启动前端

```bash
cd frontend/xwzx-news
npm install
npm run dev
```

浏览器访问终端输出的地址，默认通常为 <http://localhost:5173>。前端后端地址目前配置在 `frontend/xwzx-news/src/config/api.js`，默认连接 `http://127.0.0.1:8000`。

AI 问答是可选功能。如需启用，在 `frontend/xwzx-news/.env.local` 中配置 DashScope API Key：

```dotenv
VITE_AI_CHAT_API_KEY=your_dashscope_api_key
```

修改环境变量后需要重新启动 Vite 开发服务器。

## API 概览

### 公共接口

| 方法 | 地址 | 说明 |
| --- | --- | --- |
| `GET` | `/` | 服务状态 |
| `GET` | `/api/news/categories` | 获取新闻分类 |
| `GET` | `/api/news/list` | 按分类分页获取新闻 |
| `GET` | `/api/news/detail` | 获取新闻详情和相关推荐 |
| `POST` | `/api/user/register` | 用户注册 |
| `POST` | `/api/user/login` | 用户登录 |

### 登录后接口

下列接口需要请求头 `Authorization: Bearer <token>`。后端也兼容直接传递 token。

| 方法 | 地址 | 说明 |
| --- | --- | --- |
| `GET` | `/api/user/info` | 获取当前用户资料 |
| `PUT` | `/api/user/update` | 修改用户资料 |
| `PUT` | `/api/user/password` | 修改密码 |
| `GET` | `/api/favorite/check` | 检查收藏状态 |
| `POST` | `/api/favorite/add` | 添加收藏 |
| `DELETE` | `/api/favorite/remove` | 取消收藏 |
| `GET` | `/api/favorite/list` | 获取收藏列表 |
| `DELETE` | `/api/favorite/clear` | 清空收藏 |
| `POST` | `/api/history/add` | 添加浏览记录 |
| `GET` | `/api/history/list` | 获取浏览历史 |
| `DELETE` | `/api/history/delete/{news_id}` | 删除一条浏览记录 |
| `DELETE` | `/api/history/clear` | 清空浏览历史 |

更完整的参数、响应模型和在线调试入口请查看 Swagger；仓库中的 `test_main.http` 也提供了基础请求示例。

## 数据库说明

演示 SQL 包含以下数据表：

| 表名 | 用途 |
| --- | --- |
| `news_category` | 新闻分类 |
| `news` | 新闻内容 |
| `user` | 用户资料 |
| `user_token` | 登录令牌 |
| `favorite` | 用户收藏 |
| `history` | 浏览历史 |
| `related_news` | 相关新闻关系 |
| `ai_chat` | AI 聊天记录预留表 |

当前 AI 页面直接调用 DashScope，聊天记录尚未通过后端写入 `ai_chat` 表；相关新闻由后端按相同分类动态查询，未依赖 `related_news` 表。

## 常用命令

```bash
# 后端开发
uv run uvicorn main:app --reload

# 手动升级数据库
uv run alembic upgrade head

# 生成迁移文件（修改 ORM Model 后）
uv run alembic revision --autogenerate -m "describe change"

# 前端开发与构建
cd frontend/xwzx-news
npm run dev
npm run build
npm run preview
```

## 部署注意事项

- 不要提交 `env/.env.dev`、`.env.local`、`tmp_token.txt` 或任何真实密钥，仓库已在 `.gitignore` 中忽略这些文件。
- `VITE_*` 环境变量会被打包进浏览器代码。当前 AI 直连方式只适合学习和本地演示；生产环境应由后端代理 AI 请求并在服务端保存密钥。
- 生产环境请关闭 `DEBUG` 和 `DATABASE_ECHO`，并将 `CORS_ORIGINS` 设置为明确的前端域名。
- 前端 API 地址目前为源码中的固定值，部署时应改造成环境变量配置。
- Redis 当前使用固定的 `localhost:6379/0`。未启动 Redis 不影响核心查询，但会在控制台输出缓存连接失败信息。
- 项目目前没有自动化测试，提交生产环境前建议补充 Service、API 和前端关键流程测试。




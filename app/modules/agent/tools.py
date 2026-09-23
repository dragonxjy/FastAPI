"""Agent 的六个工具：模型选工具，Python 真正操作数据库。

这是共享文章库教学项目，所有已登录用户都可以管理文章。
模型拿不到 SQL、数据库连接或系统命令，只能调用下面定义好的函数。
"""

import asyncio

from langchain.tools import tool
from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.favorite.model import Favorite
from app.modules.history.model import History
from app.modules.news.model import Category, News


def article_data(article: News, *, with_content: bool = False) -> dict:
    """把 ORM 对象变成普通字典，模型和前端才能读懂它。"""
    data = {
        "id": article.id,
        "title": article.title,
        "description": article.description,
        "author": article.author,
        "category_id": article.category_id,
    }
    if with_content:
        # 老文章可能很长，控制工具返回量，避免把模型上下文撑满。
        data["content"] = article.content[:20000]
        data["content_truncated"] = len(article.content) > 20000
    return data


def text_error(value: str, label: str, maximum: int, *, required: bool = True):
    if required and not value.strip():
        return f"{label}不能为空。"
    if len(value) > maximum:
        return f"{label}不能超过 {maximum} 个字符。"
    return None


def build_article_tools(db: AsyncSession):
    """每次聊天创建一组工具，共用本次请求的数据库事务。

    @tool 会把函数名、注释、参数类型转换成模型能理解的工具说明。
    把工具函数写在这里，是为了让它们记住本次请求的 db（这叫“闭包”）。
    db 不在工具参数里，所以模型只需提供标题、文章 ID 等业务信息。
    锁保证模型同时调用多个工具时，它们不会同时操作同一个数据库会话。
    flush 只是把修改暂存到事务里；最终 commit / rollback 在 service.py。
    """
    lock = asyncio.Lock()

    @tool
    async def list_categories() -> dict:
        """列出可用的文章分类及分类 ID；创建文章前先查分类。"""
        async with lock:
            rows = (await db.scalars(select(Category).order_by(Category.sort_order, Category.id))).all()
            return {"ok": True, "categories": [{"id": c.id, "name": c.name} for c in rows]}

    @tool
    async def search_articles(keyword: str = "", limit: int = 10) -> dict:
        """按关键词搜索文章标题、摘要和正文，返回 ID 和摘要；空关键词列出最近文章。limit 为 1 到 20。"""
        if len(keyword) > 100 or not 1 <= limit <= 20:
            return {"ok": False, "error": "关键词最多 100 字，limit 必须是 1 到 20。"}
        async with lock:
            query = select(News)
            if keyword.strip():
                # SQLAlchemy 会绑定参数；autoescape 避免 % 和 _ 被当成通配符。
                query = query.where(or_(
                    News.title.contains(keyword.strip(), autoescape=True),
                    News.description.contains(keyword.strip(), autoescape=True),
                    News.content.contains(keyword.strip(), autoescape=True),
                ))
            rows = (await db.scalars(query.order_by(News.id.desc()).limit(limit))).all()
            return {"ok": True, "articles": [article_data(row) for row in rows], "limit": limit}

    @tool
    async def get_article(id: int) -> dict:
        """按正整数文章 ID 查看正文；修改或删除前先读取，确认目标。"""
        async with lock:
            article = await db.get(News, id) if id > 0 else None
            if not article:
                return {"ok": False, "error": f"文章 ID {id} 不存在。"}
            return {"ok": True, "article": article_data(article, with_content=True)}

    @tool
    async def create_article(title: str, content: str, category_id: int,
                             description: str = "", author: str = "AI助手") -> dict:
        """创建文章。title 最多255字，content最多20000字，description最多500字，author最多50字；分类必须存在。正文使用纯文本。"""
        for value, label, maximum, required in [
            (title, "标题", 255, True), (content, "正文", 20000, True),
            (description, "摘要", 500, False), (author, "作者", 50, False),
        ]:
            error = text_error(value, label, maximum, required=required)
            if error:
                return {"ok": False, "error": error}
        async with lock:
            if category_id <= 0 or not await db.get(Category, category_id):
                return {"ok": False, "error": "分类不存在，请先调用 list_categories。"}
            article = News(title=title.strip(), content=content.strip(),
                           category_id=category_id, description=description.strip(),
                           author=author.strip(), views=0)
            db.add(article)
            # flush 后就有数据库生成的文章 ID，模型可以继续查询或修改它。
            # 此时还没最终保存：后续模型调用失败，service.py 会统一回滚。
            await db.flush()
            return {"ok": True, "changed": True, "article": article_data(article)}

    @tool
    async def update_article(id: int, title: str | None = None, content: str | None = None,
                             category_id: int | None = None, description: str | None = None,
                             author: str | None = None) -> dict:
        """更新指定文章，只传需要修改的字段；未传的字段保持原样。长度要求与创建相同。正文使用纯文本。"""
        changes = {"title": title, "content": content, "category_id": category_id,
                   "description": description, "author": author}
        changes = {key: value for key, value in changes.items() if value is not None}
        if not changes:
            return {"ok": False, "error": "请至少提供一个需要修改的字段。"}
        for field, label, maximum, required in [
            ("title", "标题", 255, True), ("content", "正文", 20000, True),
            ("description", "摘要", 500, False), ("author", "作者", 50, False),
        ]:
            if field in changes:
                error = text_error(changes[field], label, maximum, required=required)
                if error:
                    return {"ok": False, "error": error}
        async with lock:
            article = await db.get(News, id) if id > 0 else None
            if not article:
                return {"ok": False, "error": f"文章 ID {id} 不存在。"}
            if category_id is not None and (category_id <= 0 or not await db.get(Category, category_id)):
                return {"ok": False, "error": "分类不存在，请先调用 list_categories。"}
            for field, value in changes.items():
                setattr(article, field, value.strip() if isinstance(value, str) else value)
            await db.flush()
            return {"ok": True, "changed": True, "article": article_data(article)}

    @tool
    async def delete_article(id: int) -> dict:
        """删除用户明确要求删除的文章。必须使用已查到的准确文章 ID，同时清理该文章的收藏和浏览历史。"""
        async with lock:
            article = await db.get(News, id) if id > 0 else None
            if not article:
                return {"ok": False, "error": f"文章 ID {id} 不存在。"}
            deleted_article = article_data(article)
            # 旧表没有级联删除，所以先清理引用，避免外键约束错误。
            await db.execute(delete(Favorite).where(Favorite.news_id == id))
            await db.execute(delete(History).where(History.news_id == id))
            await db.delete(article)
            await db.flush()
            return {"ok": True, "changed": True, "deleted_article": deleted_article}

    return [list_categories, search_articles, get_article, create_article, update_article, delete_article]

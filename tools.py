"""工具模块：文档处理管线 + Agent 工具定义。

文档知识库设计说明：
- 使用模块级全局变量 _faiss_db 管理 FAISS 索引（单用户 MVP）
- 多次上传文档时采用「追加合并」策略，所有文档累积到同一索引
- 对话记忆按 thread_id 隔离，但文档知识库全局共享
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import numexpr
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_core.tools import tool
from langchain_tavily import TavilySearch
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    RETRIEVER_SEARCH_TYPE,
    RETRIEVER_TOP_K,
    embeddings,
)

# ── 全局文档知识库 ──
_faiss_db: FAISS | None = None
_uploaded_files: list[str] = []

# ── 文本切分器 ──
_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", "。", "！", "？", ".", " ", ""],
)


# ═══════════════════════════════════════════
# 文档处理
# ═══════════════════════════════════════════


def process_uploaded_files(
    file_paths: list[str],
) -> tuple[int, list[str]]:
    """处理上传的文件列表，返回 (新增chunk数, 处理失败的文件及原因列表)。"""
    global _faiss_db

    total_chunks = 0
    errors: list[str] = []

    for path in file_paths:
        try:
            docs = _load_file(path)
            if not docs:
                errors.append(f"{Path(path).name}: 未提取到任何文本（可能是扫描版 PDF）")
                continue

            # 为每个 chunk 添加 metadata
            file_name = Path(path).name
            chunks = _splitter.split_documents(docs)
            for i, chunk in enumerate(chunks):
                chunk.metadata["source"] = file_name
                chunk.metadata["chunk_id"] = i

            if not chunks:
                errors.append(f"{file_name}: 切分后无有效文本块")
                continue

            # 追加合并到全局索引
            new_db = FAISS.from_documents(chunks, embeddings)
            if _faiss_db is None:
                _faiss_db = new_db
            else:
                _faiss_db.merge_from(new_db)

            _uploaded_files.append(file_name)
            total_chunks += len(chunks)

        except Exception as e:
            errors.append(f"{Path(path).name}: {e}")

    return total_chunks, errors


def _load_file(path: str) -> list:
    """根据文件扩展名加载文档，返回 Document 列表。"""
    ext = Path(path).suffix.lower()
    if ext == ".pdf":
        loader = PyPDFLoader(path)
        docs = loader.load()
        # 检查是否全为空白（扫描版 PDF）
        text = "".join(d.page_content.strip() for d in docs)
        if not text:
            return []
        return docs
    elif ext == ".txt":
        loader = TextLoader(path, encoding="utf-8")
        return loader.load()
    else:
        raise ValueError(f"不支持的文件格式: {ext}（仅支持 PDF 和 TXT）")


def get_uploaded_files() -> list[str]:
    """返回当前已上传的文件名列表。"""
    return list(_uploaded_files)


def clear_documents() -> None:
    """清空知识库索引和已上传文件记录。"""
    global _faiss_db
    _faiss_db = None
    _uploaded_files.clear()


# ═══════════════════════════════════════════
# Agent 工具
# ═══════════════════════════════════════════


@tool
def document_retriever(query: str) -> str:
    """从已上传的文档中检索相关内容。当用户的问题与已上传文档内容相关时使用此工具。"""
    if _faiss_db is None:
        return "尚未上传任何文档，请先上传 PDF 或 TXT 文件。"

    retriever = _faiss_db.as_retriever(
        search_type=RETRIEVER_SEARCH_TYPE,
        search_kwargs={"k": RETRIEVER_TOP_K},
    )
    results = retriever.invoke(query)

    if not results:
        return "在已上传的文档中未找到与该问题相关的内容。"

    # 格式化结果，附带来源信息
    parts = []
    for doc in results:
        source = doc.metadata.get("source", "未知")
        page = doc.metadata.get("page")
        loc = f"[来源: {source}" + (f", 第{page + 1}页" if page is not None else "") + "]"
        parts.append(f"{loc}\n{doc.page_content}")

    return "\n\n---\n\n".join(parts)


# 网页搜索工具
tavily_search = TavilySearch(max_results=3)

# 安全计算器表达式白名单：只允许数字、运算符、括号、小数点、空格
_SAFE_EXPR = re.compile(r"^[\d\s\+\-\*/\.\(\)\%\^]+$")


@tool
def calculator(expression: str) -> str:
    """计算数学表达式。当需要进行数学计算时使用此工具。输入示例: '(125 + 375) * 2.5'"""
    expr = expression.strip()
    if not _SAFE_EXPR.match(expr):
        return f"不安全的表达式，仅支持数字和基本运算符(+-*/^%)。收到: {expr}"
    try:
        result = numexpr.evaluate(expr)
        return f"{expr} = {result}"
    except Exception as e:
        return f"计算出错: {e}"


def get_tools() -> list:
    """返回所有 Agent 工具列表。"""
    return [document_retriever, tavily_search, calculator]

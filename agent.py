"""Agent 模块：基于 LangGraph 的 ReAct Agent，支持多轮对话与工具调用。"""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from config import llm
from tools import get_tools

SYSTEM_PROMPT = """\
你是一个智能文档问答助手。你可以使用以下工具来帮助用户：

1. document_retriever： 从用户上传的文档中检索相关内容
2. tavily_search：  在互联网上搜索最新信息
3. calculato：  进行数学计算

## 工具使用优先级

当用户的问题可能与已上传文档相关时，优先使用 document_retriever
如果文档中未找到相关内容，明确告知用户"文档中未找到相关信息"，不要自行编造
仅当用户需要实时信息或新闻时，使用 tavily_search
仅当用户需要数学计算时，使用 calculator
对于常识性问题，可以直接回答，无需调用工具

## 回答规范

使用中文回答
基于文档回答时，引用来源（文件名、页码）
回答要简洁准确，避免冗余
"""

# 对话记忆（内存级，重启后丢失）
_memory = MemorySaver()
_agent = None


def _build_agent():
    global _agent
    _agent = create_react_agent(
        model=llm,
        tools=get_tools(),
        prompt=SYSTEM_PROMPT,
        checkpointer=_memory,
    )


def rebuild_agent() -> None:
    """重建 Agent（文档上传后调用，以更新工具状态）。"""
    _build_agent()


def chat(message: str, thread_id: str) -> str:
    """发送消息给 Agent 并返回回复文本。"""
    if _agent is None:
        _build_agent()

    response = _agent.invoke(
        {"messages": [("user", message)]},
        config={"configurable": {"thread_id": thread_id}},
    )

    # 提取最后一条 AI 消息
    ai_message = response["messages"][-1]
    return ai_message.content

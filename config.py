"""配置模块：加载环境变量，初始化 LLM 和嵌入模型。"""

import os
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

# ── 文档切分参数 ──
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# ── 检索参数 ──
RETRIEVER_TOP_K = 4
RETRIEVER_SEARCH_TYPE = "mmr"  # mmr 增加结果多样性

# ── LLM ──
llm = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0,
    api_key=os.getenv("DEEPSEEK_API_KEY"),
)

# ── 嵌入模型（本地，首次运行会自动下载 ~90MB） ──
embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-zh-v1.5",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)

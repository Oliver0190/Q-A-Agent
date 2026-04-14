# RAG 智能文档问答 Agent

基于 LangChain + DeepSeek API 构建的多轮对话文档问答 Agent，支持 PDF/TXT 文档上传、自动切分与向量化检索（FAISS），集成 Agent Tool Calling 机制。

## 功能特性

- **文档问答**：上传 PDF/TXT 文档，自动切分并向量化，基于语义检索回答问题
- **Agent 工具调用**：由 Agent 自主决策调用文档检索、网页搜索或计算器
- **多轮对话**：支持上下文记忆，可进行连续追问
- **引用溯源**：回答时标注信息来源（文件名、页码）
- **交互界面**：Gradio 构建的 Web UI，支持文件上传与实时对话

## 技术栈

| 组件 | 技术选型 |
|------|---------|
| LLM | DeepSeek V3 (deepseek-chat) |
| 框架 | LangChain + LangGraph |
| 向量数据库 | FAISS |
| 嵌入模型 | BAAI/bge-small-zh-v1.5 (本地) |
| 网页搜索 | Tavily Search API |
| 前端 | Gradio |

## 快速启动

### 1. 克隆项目

```bash
git clone https://github.com/Oliver0190/Q-A-Agent.git
cd RAG-Agent
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

编辑 `.env` 文件，填入你的 API Key：

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

- DeepSeek API Key：[platform.deepseek.com](https://platform.deepseek.com)
- Tavily API Key：[tavily.com](https://tavily.com)

### 4. 启动应用

```bash
python app.py
```

打开浏览器访问 `http://127.0.0.1:7860`

## 使用说明

1. 在左侧上传 PDF 或 TXT 文档，点击「上传并处理」
2. 在右侧输入问题，Agent 会自动判断使用哪个工具回答
3. 支持多文件上传，知识库会累积合并
4. 点击「清空知识库」可重置文档索引

## 项目结构

```
├── config.py        # 配置与模型初始化
├── tools.py         # 文档处理 + 工具定义
├── agent.py         # ReAct Agent 核心逻辑
├── app.py           # Gradio UI 入口
├── requirements.txt # Python 依赖
└── .env             # API 密钥
```

"""Gradio UI 入口：文档上传 + 智能问答交互界面。"""

import uuid

import gradio as gr

from agent import chat, rebuild_agent
from tools import clear_documents, get_uploaded_files, process_uploaded_files

# ═══════════════════════════════════════════════════
# CSS：精致现代风格，接近 Claude / ChatGPT 质感
# ═══════════════════════════════════════════════════
CUSTOM_CSS = """
/* ── 设计令牌 ── */
:root {
    --bg-page:        #f8f8f7;
    --bg-card:        #ffffff;
    --bg-hover:       #f5f5f4;
    --border-light:   #e8e5e0;
    --border-focus:   #c4bfb8;
    --text-primary:   #1a1a1a;
    --text-secondary: #8c8c8c;
    --text-placeholder:#b5b5b5;
    --accent:         #6b5ce7;
    --accent-hover:   #5a4bd6;
    --radius-sm:      8px;
    --radius-md:      12px;
    --radius-lg:      20px;
    --shadow-sm:      0 1px 3px rgba(0,0,0,0.04);
    --shadow-md:      0 2px 8px rgba(0,0,0,0.06);
    --shadow-focus:   0 0 0 3px rgba(107,92,231,0.08);
    --font-sans:      -apple-system, BlinkMacSystemFont, "Segoe UI",
                      "PingFang SC", "Noto Sans SC", sans-serif;
}

/* ── 页面背景 ── */
.gradio-container {
    background: var(--bg-page) !important;
    font-family: var(--font-sans) !important;
    max-width: 1400px !important;
}

/* ── 标题区 ── */
.title-text h1 {
    font-size: 22px !important;
    font-weight: 700 !important;
    color: var(--text-primary) !important;
    letter-spacing: -0.3px;
    margin: 0 0 2px 0 !important;
}
.subtitle-text p {
    font-size: 13.5px !important;
    color: var(--text-secondary) !important;
    margin: 0 0 16px 0 !important;
    line-height: 1.5;
}

/* ── 统一卡片风格：所有面板 ── */
.card-panel,
.card-panel > .gr-group,
.card-panel > div > .gr-file-upload {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-light) !important;
    border-radius: var(--radius-md) !important;
    box-shadow: var(--shadow-sm) !important;
}

/* ── 左侧上传区细化 ── */
.upload-area {
    padding: 4px !important;
}
.upload-area label span {
    font-size: 13px !important;
    color: var(--text-secondary) !important;
}
/* 上传按钮 */
.upload-btn {
    border-radius: var(--radius-sm) !important;
    font-size: 13.5px !important;
    font-weight: 500 !important;
    padding: 8px 0 !important;
    background: var(--accent) !important;
    border: none !important;
    color: #fff !important;
    box-shadow: none !important;
    transition: background 0.15s ease !important;
}
.upload-btn:hover {
    background: var(--accent-hover) !important;
}
.clear-btn {
    border-radius: var(--radius-sm) !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 7px 0 !important;
    background: transparent !important;
    border: 1px solid var(--border-light) !important;
    color: var(--text-secondary) !important;
    box-shadow: none !important;
    transition: all 0.15s ease !important;
}
.clear-btn:hover {
    background: var(--bg-hover) !important;
    border-color: var(--border-focus) !important;
    color: var(--text-primary) !important;
}
/* 文档状态 */
.status-box textarea {
    font-size: 12.5px !important;
    color: var(--text-secondary) !important;
    background: var(--bg-page) !important;
    border: 1px solid var(--border-light) !important;
    border-radius: var(--radius-sm) !important;
}
.status-box label span {
    font-size: 12px !important;
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
}

/* ── 聊天气泡区 ── */
.chat-area {
    border: 1px solid var(--border-light) !important;
    border-radius: var(--radius-md) !important;
    background: var(--bg-card) !important;
    box-shadow: var(--shadow-sm) !important;
}
.chat-area .chatbot {
    background: transparent !important;
}

/* ── Chat Composer 容器 ── */
.composer {
    border: 1px solid var(--border-light) !important;
    border-radius: var(--radius-lg) !important;
    background: var(--bg-card) !important;
    box-shadow: var(--shadow-md) !important;
    padding: 0 !important;
    overflow: hidden;
    margin-top: 10px !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}
.composer:focus-within {
    border-color: var(--border-focus) !important;
    box-shadow: var(--shadow-md), var(--shadow-focus) !important;
}
/* 去掉 Group 内部默认间距 */
.composer > div {
    gap: 0 !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

/* ── Composer textarea ── */
.composer-input {
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
}
.composer-input textarea {
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
    background: transparent !important;
    padding: 18px 20px 10px 20px !important;
    font-size: 14.5px !important;
    line-height: 1.6 !important;
    color: var(--text-primary) !important;
    resize: none !important;
    min-height: 48px !important;
    font-family: var(--font-sans) !important;
}
.composer-input textarea::placeholder {
    color: var(--text-placeholder) !important;
    font-weight: 400 !important;
}

/* ── Composer 工具栏 ── */
.composer-toolbar {
    padding: 2px 12px 10px 12px !important;
    background: transparent !important;
    border: none !important;
    border-top: none !important;
    gap: 6px !important;
    align-items: center !important;
    box-shadow: none !important;
}

/* + 按钮 */
.tb-plus {
    min-width: 28px !important;
    max-width: 28px !important;
    height: 28px !important;
    padding: 0 !important;
    border-radius: 8px !important;
    font-size: 16px !important;
    font-weight: 400 !important;
    border: 1px solid var(--border-light) !important;
    background: transparent !important;
    color: var(--text-secondary) !important;
    cursor: pointer !important;
    box-shadow: none !important;
    transition: all 0.15s ease !important;
    line-height: 26px !important;
    text-align: center !important;
}
.tb-plus:hover {
    background: var(--bg-hover) !important;
    color: var(--text-primary) !important;
}

/* 模型标签 capsule */
.tb-model {
    min-width: auto !important;
    height: 28px !important;
    padding: 0 10px !important;
    border-radius: 14px !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    border: 1px solid var(--border-light) !important;
    background: var(--bg-page) !important;
    color: var(--text-secondary) !important;
    cursor: default !important;
    box-shadow: none !important;
    letter-spacing: 0.2px !important;
    line-height: 26px !important;
}

/* 弹簧占位 */
.toolbar-spacer {
    flex: 1 !important;
    min-width: 0 !important;
}

/* 发送图标 */
.send-icon {
    min-width: 30px !important;
    max-width: 30px !important;
    height: 30px !important;
    padding: 0 !important;
    border-radius: 9px !important;
    font-size: 14px !important;
    border: none !important;
    background: var(--text-primary) !important;
    color: #ffffff !important;
    cursor: pointer !important;
    box-shadow: none !important;
    transition: opacity 0.15s ease !important;
    line-height: 30px !important;
    text-align: center !important;
}
.send-icon:hover {
    opacity: 0.8 !important;
}

/* ── 全局按钮重置 ── */
button {
    transition: all 0.15s ease !important;
}

/* ── label 统一 ── */
.gradio-container label span {
    font-weight: 500 !important;
}

/* ── 移动端适配 ── */
@media (max-width: 768px) {
    .gradio-container {
        padding: 8px !important;
    }
    .composer-input textarea {
        padding: 14px 16px 8px 16px !important;
        font-size: 14px !important;
    }
    .composer-toolbar {
        padding: 2px 8px 8px 8px !important;
    }
}
"""


def handle_upload(files):
    """处理文件上传，返回状态文本。"""
    if not files:
        return "请选择文件上传"

    file_paths = [f.name if hasattr(f, "name") else str(f) for f in files]
    chunk_count, errors = process_uploaded_files(file_paths)

    rebuild_agent()

    lines = []
    if chunk_count > 0:
        lines.append(f"✓ 成功处理 {chunk_count} 个文本块")
    for err in errors:
        lines.append(f"✗ {err}")

    uploaded = get_uploaded_files()
    if uploaded:
        lines.append(f"\n当前知识库文档: {', '.join(uploaded)}")

    return "\n".join(lines)


def handle_clear_docs():
    """清空知识库。"""
    clear_documents()
    rebuild_agent()
    return "知识库已清空"


def handle_chat(message, history, session_id):
    """处理用户消息，返回 Agent 回复。"""
    if not message.strip():
        return history, ""

    try:
        reply = chat(message, session_id)
    except Exception as e:
        reply = f"出错了: {e}"

    history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": reply},
    ]
    return history, ""


def handle_new_chat(session_id):
    """开启新对话：清空聊天记录，生成新的 session_id。"""
    return [], str(uuid.uuid4())


# ── 构建 Gradio 界面 ──
with gr.Blocks(title="RAG 智能问答助手") as demo:
    gr.Markdown("# RAG 智能问答助手", elem_classes="title-text")
    gr.Markdown(
        "上传 PDF 或 TXT 文档，向 AI 提问 · 支持文档检索、网页搜索、数学计算",
        elem_classes="subtitle-text",
    )

    session_id = gr.State(lambda: str(uuid.uuid4()))

    with gr.Row():
        # ── 左侧：文档管理 ──
        with gr.Column(scale=1, elem_classes="upload-area"):
            file_upload = gr.File(
                label="上传文档（PDF / TXT）",
                file_types=[".pdf", ".txt"],
                file_count="multiple",
            )
            upload_btn = gr.Button(
                "上传并处理", variant="primary", elem_classes="upload-btn"
            )
            clear_doc_btn = gr.Button(
                "清空知识库", variant="secondary", elem_classes="clear-btn"
            )
            upload_status = gr.Textbox(
                label="文档状态",
                interactive=False,
                lines=4,
                elem_classes="status-box",
            )

        # ── 右侧：聊天 ──
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                label="对话",
                height=470,
                elem_classes="chat-area",
            )

            # ── Chat Composer ──
            with gr.Group(elem_classes="composer"):
                msg = gr.Textbox(
                    placeholder="输入你的问题...",
                    show_label=False,
                    lines=2,
                    max_lines=6,
                    container=False,
                    elem_classes="composer-input",
                )
                with gr.Row(elem_classes="composer-toolbar"):
                    new_chat_btn = gr.Button(
                        "+", scale=0, elem_classes="tb-plus",
                    )
                    gr.Button(
                        "DeepSeek V3",
                        scale=0,
                        interactive=False,
                        elem_classes="tb-model",
                    )
                    gr.HTML("<span class='toolbar-spacer'></span>")
                    submit_btn = gr.Button(
                        "↑", scale=0, elem_classes="send-icon",
                    )

    # ── 事件绑定 ──
    upload_btn.click(
        fn=handle_upload,
        inputs=[file_upload],
        outputs=[upload_status],
    )
    clear_doc_btn.click(
        fn=handle_clear_docs,
        outputs=[upload_status],
    )
    submit_btn.click(
        fn=handle_chat,
        inputs=[msg, chatbot, session_id],
        outputs=[chatbot, msg],
    )
    msg.submit(
        fn=handle_chat,
        inputs=[msg, chatbot, session_id],
        outputs=[chatbot, msg],
    )
    new_chat_btn.click(
        fn=handle_new_chat,
        inputs=[session_id],
        outputs=[chatbot, session_id],
    )

if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft(), css=CUSTOM_CSS)

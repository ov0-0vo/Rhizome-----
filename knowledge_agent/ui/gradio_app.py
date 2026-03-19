import gradio as gr
from typing import List, Dict, Any

from knowledge_agent.agent.qa_agent import QAAgent
from knowledge_agent.knowledge.catalog_manager import CatalogManager


class KnowledgeAgentUI:
    def __init__(self):
        self.agent = QAAgent()
        self.catalog_manager = CatalogManager()
        self.conversation_history = []

    def chat(self, message: str, history: List[List[str]]) -> str:
        if not message.strip():
            return ""
        
        history.append([message, ""])
        
        try:
            result = self.agent.chat(message)
            
            answer = result["answer"]
            
            if result.get("is_new"):
                catalog_info = ""
                if result.get("catalog_id"):
                    catalog = self.catalog_manager.get_catalog(result["catalog_id"])
                    if catalog:
                        catalog_info = f"\n\n📁 已整理到知识目录: **{catalog.name}**"
                answer += catalog_info
            
            history[-1][1] = answer
            
        except Exception as e:
            history[-1][1] = f"抱歉，处理您的问题时出现错误: {str(e)}"
        
        return "", history

    def get_knowledge_tree_display(self) -> str:
        tree = self.agent.get_knowledge_tree()
        
        if not tree:
            return "📚 知识目录为空，开始提问来建立您的知识体系吧！"
        
        def format_tree(node: Dict, level: int = 0) -> str:
            indent = "  " * level
            prefix = "📂 " if level == 0 else "📁 "
            text = f"{indent}{prefix}{node.get('name', '未命名')}"
            text += f" ({node.get('knowledge_count', 0)} 条知识)\n"
            
            for child in node.get("children", []):
                text += format_tree(child, level + 1)
            
            return text
        
        header = "# 📚 知识体系目录\n\n"
        return header + format_tree(tree)

    def get_statistics_display(self) -> str:
        stats = self.agent.get_statistics()
        
        text = "# 📊 知识库统计\n\n"
        text += f"- **总知识条目**: {stats['total_knowledge']}\n"
        text += f"- **知识目录数**: {stats['catalogs_count']}\n\n"
        
        if stats.get("latest_knowledge"):
            text += "### 最近添加的知识:\n\n"
            for item in stats['latest_knowledge']:
                text += f"- {item['question']}\n"
                text += f"  - 添加时间: {item['created_at'][:19]}\n\n"
        
        return text

    def search_knowledge(self, query: str) -> str:
        if not query.strip():
            return "请输入搜索关键词"
        
        results = self.agent.search_knowledge(query)
        
        if not results:
            return f"未找到与 '{query}' 相关的知识"
        
        text = f"# 🔍 搜索结果: {query}\n\n"
        text += f"找到 {len(results)} 条相关知识:\n\n"
        
        for i, item in enumerate(results, 1):
            text += f"### {i}. {item['question']}\n"
            text += f"**答案**: {item['answer'][:200]}"
            if len(item['answer']) > 200:
                text += "..."
            text += f"\n**相似度**: {item['similarity']:.2%}\n\n"
            text += "---\n\n"
        
        return text

    def build_interface(self):
        with gr.Blocks(title="Rhizome（灵犀树）", theme=gr.themes.Soft()) as app:
            gr.Markdown("# 🌳 Rhizome（灵犀树）")
            gr.Markdown("通过对话建立和管理您的个人知识体系")
            
            with gr.Tab("💬 对话"):
                chatbot = gr.Chatbot(
                    label="对话历史",
                    height=500
                )
                with gr.Row():
                    msg_input = gr.Textbox(
                        label="请输入您的问题",
                        placeholder="例如：什么是机器学习？",
                        scale=4
                    )
                    submit_btn = gr.Button("发送", variant="primary", scale=1)
                
                submit_btn.click(
                    fn=self.chat,
                    inputs=[msg_input, chatbot],
                    outputs=[msg_input, chatbot]
                )
                msg_input.submit(
                    fn=self.chat,
                    inputs=[msg_input, chatbot],
                    outputs=[msg_input, chatbot]
                )
            
            with gr.Tab("📚 知识目录"):
                gr.Markdown(self.get_knowledge_tree_display())
                gr.Button("🔄 刷新", onclick=lambda: self.get_knowledge_tree_display())
            
            with gr.Tab("📊 知识统计"):
                gr.Markdown(self.get_statistics_display())
                gr.Button("🔄 刷新", onclick=lambda: self.get_statistics_display())
            
            with gr.Tab("🔍 知识搜索"):
                search_input = gr.Textbox(label="搜索关键词")
                search_btn = gr.Button("搜索")
                search_output = gr.Markdown()
                
                search_btn.click(
                    fn=self.search_knowledge,
                    inputs=search_input,
                    outputs=search_output
                )
                search_input.submit(
                    fn=self.search_knowledge,
                    inputs=search_input,
                    outputs=search_output
                )
        
        return app


def create_app():
    ui = KnowledgeAgentUI()
    return ui.build_interface()


if __name__ == "__main__":
    app = create_app()
    app.launch(server_name="0.0.0.0", server_port=7860)

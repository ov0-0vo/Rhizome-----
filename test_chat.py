import sys
sys.path.insert(0, '.')

from knowledge_agent.agent.qa_agent import QAAgent
from knowledge_agent.config import config


def test_chat():
    print("=" * 50)
    print("QAAgent 对话功能测试")
    print("=" * 50)
    
    print(f"\n配置信息:")
    print(f"  Provider: {config.provider}")
    print(f"  Model: {config.openai_model}")
    print(f"  API Base: {config.openai_api_base}")
    
    print("\n正在初始化 QAAgent...")
    try:
        agent = QAAgent()
        print("QAAgent 初始化成功!")
    except Exception as e:
        print(f"QAAgent 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    test_questions = [
        "你是谁？",
        "我喜欢冰淇淋？",
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*50}")
        print(f"测试 {i}: {question}")
        print("-" * 50)
        try:
            result = agent.chat(question)
            answer = result['answer']
            if len(answer) > 300:
                answer = answer[:300] + "..."
            print(f"回答: {answer}")
            print(f"来源: {result['source']}")
            print(f"是否新知识: {result['is_new']}")
        except Exception as e:
            print(f"测试失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)


if __name__ == "__main__":
    test_chat()

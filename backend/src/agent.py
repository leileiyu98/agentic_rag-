"""RAG Agent - 智能对话 Agent

使用数据库持久化对话历史
"""

from backend.src.rag_graph import build_rag_graph, run_rag
from langchain.chat_models import init_chat_model
from langchain_core.tools import Tool
from langgraph.prebuilt import create_react_agent
import os
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

# 数据库相关导入
from backend.db.connection import DatabaseConnection
from backend.db.services import MemoryService

load_dotenv()

# 全局数据库连接
db_connection = DatabaseConnection()


# ==================== RAG工具定义 ====================


def rag_tool_func(query: str) -> str:
    """
    RAG检索工具：使用知识库回答问题

    Args:
        query: 用户查询问题

    Returns:
        基于知识库的答案
    """
    try:
        print(f"[DEBUG] RAG tool called with query: {query[:50]}...")
        result = run_rag(query)
        print(
            f"[DEBUG] RAG result: {result.get('route', 'unknown')}, docs: {result.get('docs_count', 0)}"
        )

        # 构建工具返回结果
        answer = result.get("answer", "")
        trace = result.get("trace", {})

        # 添加trace信息供调试
        debug_info = f"\n\n[Debug] Route: {result.get('route')}, Expansion: {result.get('expansion_type')}, Docs: {result.get('docs_count')}"

        return answer + debug_info

    except Exception as e:
        import traceback

        error_detail = traceback.format_exc()
        print(f"[ERROR] RAG tool error: {e}\n{error_detail}")
        return f"检索知识库时出错: {str(e)}"


# 定义RAG工具
rag_tool = Tool(
    name="knowledge_base_search",
    func=rag_tool_func,
    description="""使用知识库检索工具回答问题。
    
    当你需要回答关于特定领域知识的问题时使用此工具。
    工具会:
    1. 检索相关文档
    2. 评估文档相关性
    3. 必要时重写查询以获取更好的结果
    4. 基于检索到的信息生成回答
    
    输入: 用户的自然语言问题
    输出: 基于知识库的答案
    """,
)


# ==================== Agent创建 ====================


def create_agent_instance():
    """
    创建Agent实例
    """
    try:
        print("[DEBUG] Creating agent instance...")
        # 初始化LLM模型
        model = init_chat_model(
            model=os.getenv("LLM_MODEL", "gpt-4-0613"),
            model_provider=os.getenv("LLM_PROVIDER", "openai"),
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            temperature=0.7,
            stream_usage=True,
        )
        print(f"[DEBUG] LLM model initialized: {os.getenv('LLM_MODEL', 'gpt-4-0613')}")

        # 定义工具列表
        tools = [rag_tool]
        print(f"[DEBUG] Tools initialized: {[t.name for t in tools]}")

        # 创建系统提示
        system_prompt = """你是一个智能助手，擅长回答各种问题。

你有以下工具可用:
1. knowledge_base_search - 知识库检索工具

指导原则:
- 当用户询问需要专业知识的问题时，使用 knowledge_base_search 工具
- 对于简单的问候、闲聊或常识性问题，直接回答
- 使用工具时，提供清晰、具体的问题描述
- 基于工具返回的信息，给出完整、准确的回答
- 如果工具没有找到相关信息，坦诚告知用户

始终保持友好、专业的态度。
"""

        # 使用 create_react_agent 创建 Agent (新版 LangGraph)
        agent_executor = create_react_agent(model, tools, prompt=system_prompt)
        print("[DEBUG] Agent executor created successfully")

        return model, agent_executor
    except Exception as e:
        import traceback

        print(f"[ERROR] Failed to create agent: {e}")
        traceback.print_exc()
        raise


# 全局Agent实例（按需初始化）
_agent_instance = None


def get_agent():
    """获取或创建Agent实例（单例模式）"""
    global _agent_instance
    if _agent_instance is None:
        print("[DEBUG] Creating new agent instance...")
        try:
            _, _agent_instance = create_agent_instance()
            print("[DEBUG] Agent instance created successfully")
        except Exception as e:
            print(f"[ERROR] Failed to create agent instance: {e}")
            raise
    return _agent_instance


# ==================== 持久化对话历史 ====================


class PersistentMemory:
    """数据库持久化的对话历史管理"""

    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
        self._max_history = 20  # 每次对话保留的最大历史消息数

    def get_history(self, user_id: str, session_id: str) -> List[Dict[str, str]]:
        """
        获取对话历史

        Args:
            user_id: 用户ID
            session_id: 会话ID

        Returns:
            LangChain 格式的消息列表
        """
        session = self.db.get_session()
        try:
            service = MemoryService(session)
            # 获取最近N条历史消息
            history = service.get_conversation_history(
                session_id=session_id,
                limit=self._max_history,
                include_system=False,  # 不将系统消息传给 LLM
            )
            return history
        except Exception as e:
            print(f"获取对话历史失败: {e}")
            return []
        finally:
            session.close()

    def add_message(
        self,
        user_id: str,
        session_id: str,
        role: str,
        content: str,
        metadata: Dict = None,
    ):
        """
        添加消息到历史

        Args:
            user_id: 用户ID
            session_id: 会话ID
            role: 角色 (user/assistant/system)
            content: 消息内容
            metadata: 额外元数据
        """
        session = self.db.get_session()
        try:
            service = MemoryService(session)
            service.add_message(
                session_id=session_id,
                role=role,
                content=content,
                user_id=user_id,
                metadata=metadata,
            )
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"添加消息失败: {e}")
        finally:
            session.close()

    def clear(self, user_id: str, session_id: str) -> bool:
        """
        清除对话历史

        Args:
            user_id: 用户ID
            session_id: 会话ID

        Returns:
            是否成功清除
        """
        session = self.db.get_session()
        try:
            service = MemoryService(session)
            deleted_count = service.clear_conversation(session_id)
            session.commit()
            return deleted_count > 0
        except Exception as e:
            session.rollback()
            print(f"清除对话历史失败: {e}")
            return False
        finally:
            session.close()


# 全局内存存储（使用数据库持久化）
_memory_store = PersistentMemory(db_connection)


# ==================== 对话函数 ====================


def chat_with_agent(query: str, user_id: str = "default", session_id: str = "default") -> dict:
    """
    与Agent对话

    Args:
        query: 用户输入
        user_id: 用户ID
        session_id: 会话ID

    Returns:
        包含回答和元信息的字典
    """
    try:
        agent = get_agent()

        # 获取对话历史
        chat_history = _memory_store.get_history(user_id, session_id)
        print(f"[DEBUG] Got {len(chat_history)} history messages")

        # 确保历史记录格式正确
        formatted_history = []
        for msg in chat_history:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                formatted_history.append({"role": msg["role"], "content": msg["content"]})
            else:
                print(f"[WARN] Skipping invalid history message: {msg}")

        print(f"[DEBUG] Formatted {len(formatted_history)} history messages")
        # 调用Agent (新版 LangGraph create_react_agent)
        messages = formatted_history + [{"role": "user", "content": query}]
        print(f"[DEBUG] Sending {len(messages)} messages to agent")
        print(f"[DEBUG] Message format: {messages}")

        try:
            response = agent.invoke({"messages": messages})
            print(f"[DEBUG] Agent response received: {type(response)}")
        except Exception as agent_error:
            import traceback

            print(f"[ERROR] Agent invoke failed: {agent_error}")
            traceback.print_exc()
            raise agent_error

        # 从响应中提取最后一条消息的内容
        response_messages = response.get("messages", [])
        if response_messages:
            last_message = response_messages[-1]
            answer = getattr(last_message, "content", str(last_message))
        else:
            answer = "抱歉，我没有理解您的问题。"

        # 更新数据库中的对话历史
        _memory_store.add_message(user_id, session_id, "user", query)
        _memory_store.add_message(
            user_id,
            session_id,
            "assistant",
            answer,
            metadata={"used_rag": "knowledge_base_search" in answer},
        )

        return {
            "answer": answer,
            "success": True,
            "user_id": user_id,
            "session_id": session_id,
        }

    except Exception as e:
        return {
            "answer": f"处理请求时出错: {str(e)}",
            "success": False,
            "error": str(e),
            "user_id": user_id,
            "session_id": session_id,
        }


def clear_conversation(user_id: str = "default", session_id: str = "default") -> dict:
    """
    清除对话历史

    Args:
        user_id: 用户ID
        session_id: 会话ID

    Returns:
        操作结果字典
    """
    success = _memory_store.clear(user_id, session_id)
    return {
        "success": success,
        "message": "对话历史已清除" if success else "清除失败或无历史记录",
    }


# ==================== 对话历史管理接口 ====================


def get_conversation_history(
    user_id: str,
    session_id: str,
    limit: int = 100,
    detail: bool = False,
) -> Dict[str, Any]:
    """
    获取对话历史详情

    Args:
        user_id: 用户ID
        session_id: 会话ID
        limit: 返回消息数量限制
        detail: 是否返回完整详情（包含元数据）

    Returns:
        对话历史字典
    """
    session = db_connection.get_session()
    try:
        service = MemoryService(session)

        messages = service.get_conversation_history(session_id, limit=limit)

        return {
            "success": True,
            "user_id": user_id,
            "session_id": session_id,
            "messages": messages,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
    finally:
        session.close()


def list_user_conversations(user_id: str, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """
    获取用户的所有会话列表

    Args:
        user_id: 用户ID
        limit: 返回数量限制
        offset: 偏移量

    Returns:
        会话列表
    """
    session = db_connection.get_session()
    try:
        service = MemoryService(session)
        conversations = service.get_user_conversations(user_id, limit=limit, offset=offset)

        return {
            "success": True,
            "user_id": user_id,
            "conversations": conversations,
            "total": len(conversations),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
    finally:
        session.close()


def search_conversations(
    keyword: str,
    user_id: str = None,
    session_id: str = None,
    limit: int = 50,
) -> Dict[str, Any]:
    """
    搜索对话内容

    Args:
        keyword: 搜索关键词
        user_id: 限定用户ID（可选）
        session_id: 限定会话ID（可选）
        limit: 返回数量限制

    Returns:
        搜索结果列表
    """
    session = db_connection.get_session()
    try:
        service = MemoryService(session)
        results = service.search_conversations(
            keyword=keyword, session_id=session_id, user_id=user_id, limit=limit
        )

        return {
            "success": True,
            "keyword": keyword,
            "results": results,
            "total": len(results),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
    finally:
        session.close()


# ==================== 直接使用RAG（绕过Agent） ====================


def direct_rag_query(question: str) -> dict:
    """
    直接使用RAG回答问题（不经过Agent决策）

    适合确定需要检索知识库的场景
    """
    return run_rag(question)


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("=" * 50)
    print("RAG Agent 系统")
    print("=" * 50)
    print("\n可用功能:")
    print("1. chat_with_agent(query, user_id, session_id) - 通过Agent对话")
    print("2. direct_rag_query(question) - 直接使用RAG检索")
    print("3. clear_conversation(user_id, session_id) - 清除对话历史")
    print("4. get_conversation_history(user_id, session_id) - 获取对话历史")
    print("5. list_user_conversations(user_id) - 获取用户会话列表")
    print("6. search_conversations(keyword) - 搜索对话内容")
    print("\n使用示例:")
    print('result = chat_with_agent("什么是RAG技术？", "user_001", "session_001")')
    print('print(result["answer"])')
    print("\n" + "=" * 50)

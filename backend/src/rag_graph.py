from typing import TypedDict, List, Optional, Literal
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from backend.src.embeddings import DashScopeEmbeddings
from backend.src.sparse_embeddings import (
    convert_to_milvus_sparse_format,
    get_bm25_generator,
)
import json
import os
from dotenv import load_dotenv
from scipy import sparse
import numpy as np

load_dotenv()

# ==================== 数据模型定义 ====================


class GradeDocument(BaseModel):
    """文档相关性评分模型"""

    binary_score: str = Field(description="相关性评分: 'yes' 表示相关, 'no' 表示不相关")
    reason: str = Field(description="评分的理由")


class RewriteStrategy(BaseModel):
    """查询重写策略模型"""

    strategy: Literal["step_back", "hyde", "complex"] = Field(
        description="策略选项:\n- step_back: 退一步思考，从通用概念层面提问\n- hyde: Hypothetical Document Embedding，生成假设文档\n- complex: 复杂策略，结合 step_back + hyde"
    )
    reason: str = Field(description="选择该策略的理由")


class StepBackResult(BaseModel):
    """退一步思考结果"""

    step_back_question: str = Field(description="退一步后的通用问题")
    step_back_answer: str = Field(description="对通用问题的回答")


class HypotheticalDoc(BaseModel):
    """假设文档模型"""

    hypothetical_document: str = Field(description="假设的理想回答文档")


# ==================== 状态定义 ====================


class RAGstate(TypedDict):
    question: str  # 原始问题
    query: str  # 检索查询
    context: str  # 检索上下文
    docs: List[dict]  # 检索结果
    graded_docs: List[dict]  # 评分后的文档
    route: Optional[str]  # 路由选择
    expansion_type: Optional[str]  # 查询扩展类型
    expanded_query: Optional[str]  # 扩展后的查询
    step_back_question: Optional[str]  # 退一步问题
    step_back_answer: Optional[str]  # 退一步答案
    hypothetical_doc: Optional[str]  # 假设文档
    rag_trace: Optional[dict]  # RAG trace信息


# ==================== 初始化模型和客户端 ====================

# Embedding模型 - 使用 DashScope
embeddings = DashScopeEmbeddings(
    model=os.getenv("EMBEDDING_MODEL", "text-embedding-v3"),
    api_key=os.getenv("EMBEDDING_API_KEY"),
    base_url=os.getenv("EMBEDDING_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
)

# LLM模型 - 使用 Moonshot (OpenAI 兼容模式)
llm = init_chat_model(
    model=os.getenv("LLM_MODEL", "gpt-4"),
    model_provider=os.getenv("LLM_PROVIDER", "openai"),
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    temperature=float(os.getenv("TEMPERATURE", "0.3")),
)

# 结构化输出模型
grade_llm = llm.with_structured_output(GradeDocument)
strategy_llm = llm.with_structured_output(RewriteStrategy)
step_back_llm = llm.with_structured_output(StepBackResult)
hyde_llm = llm.with_structured_output(HypotheticalDoc)

# ==================== 节点函数实现 ====================


def retrieve_initial(state: RAGstate, use_hybrid: bool = True) -> RAGstate:
    """
    初始检索节点：使用混合检索（稠密向量 + BM25稀疏向量）检索文档
    """
    question = state["question"]

    # 生成查询稠密向量
    query_dense_embedding = embeddings.embed_query(question)

    # 从Milvus检索
    try:
        from backend.milvus.client import get_milvus_client

        client = get_milvus_client()

        if use_hybrid:
            # 生成查询稀疏向量（BM25）
            try:
                from backend.src.sparse_embeddings import (
                    get_bm25_generator,
                    convert_to_milvus_sparse_format,
                )
                from scipy import sparse
                import numpy as np

                bm25_generator = get_bm25_generator()
                # 尝试编码查询，如果模型未训练则使用空向量
                if bm25_generator.retriever is not None:
                    sparse_dict = bm25_generator.encode_query(question)
                    query_sparse_embedding = convert_to_milvus_sparse_format(sparse_dict)
                else:
                    # 创建空稀疏矩阵
                    query_sparse_embedding = sparse.csr_matrix((1, 1), dtype=np.float32)
            except Exception as e:
                print(f"BM25编码失败，回退到稠密检索: {e}")
                query_sparse_embedding = sparse.csr_matrix((1, 1), dtype=np.float32)

            # 使用混合检索
            results = client.hybrid_search(
                collection_name="document_chunks",
                query_dense_embedding=query_dense_embedding,
                query_sparse_embedding=query_sparse_embedding,
                top_k=5,
            )
            retrieval_type = "hybrid"
        else:
            # 使用纯稠密检索
            results = client.search(
                collection_name="document_chunks",
                query_embedding=query_dense_embedding,
                top_k=5,
            )
            retrieval_type = "dense"

        # 构建文档列表
        docs = []
        for idx, result in enumerate(results):
            docs.append(
                {
                    "id": result["chunk_id"],
                    "content": result["content"],
                    "score": result.get("score", 0.0),
                    "rrf_score": result.get("rrf_score"),
                    "metadata": json.loads(result.get("metadata", "{}")),
                    "source": result.get("source", ""),
                    "doc_type": result.get("doc_type", "text"),
                }
            )

        # 更新状态
        state["docs"] = docs
        state["query"] = question
        state["rag_trace"] = {
            "step": "initial_retrieval",
            "retrieval_type": retrieval_type,
            "query": question,
            "retrieved_count": len(docs),
        }

    except Exception as e:
        print(f"Retrieval error: {e}")
        import traceback

        traceback.print_exc()
        state["docs"] = []
        state["rag_trace"] = {"step": "initial_retrieval", "error": str(e)}

    return state


def grade_documents_node(state: RAGstate) -> RAGstate:
    """
    文档评分节点：评估检索到的文档与问题的相关性
    决定是否需要进行查询重写
    """
    question = state["question"]
    docs = state.get("docs", [])

    if not docs:
        # 没有检索到文档，直接路由到重写
        state["route"] = "rewrite_question"
        state["graded_docs"] = []
        return state

    # 评分提示模板
    grade_prompt = """评估以下文档是否与用户问题相关。
    
用户问题: {question}

文档内容: {content}

请判断该文档是否包含回答用户问题所需的信息。
回复格式必须是JSON，包含:
- binary_score: "yes" 或 "no"
- reason: 评分的理由
"""

    graded_docs = []
    relevant_count = 0

    for doc in docs:
        content = doc.get("content", "")

        try:
            # 使用结构化输出进行评分
            result = grade_llm.invoke(grade_prompt.format(question=question, content=content))

            doc["is_relevant"] = result.binary_score.lower() == "yes"
            doc["grade_reason"] = result.reason
            graded_docs.append(doc)

            if doc["is_relevant"]:
                relevant_count += 1

        except Exception as e:
            print(f"Grading error for doc {doc.get('id')}: {e}")
            # 评分失败时默认认为不相关
            doc["is_relevant"] = False
            doc["grade_reason"] = f"Grading failed: {str(e)}"
            graded_docs.append(doc)

    state["graded_docs"] = graded_docs

    # 决策：如果有足够相关的文档，直接生成答案；否则需要重写查询
    if relevant_count >= 2:  # 至少有2个相关文档
        state["route"] = "generate_answer"
        # 构建上下文（只使用相关文档）
        context = "\n\n".join(
            [
                f"[Document {i + 1}] {doc['content']}"
                for i, doc in enumerate(graded_docs)
                if doc.get("is_relevant", False)
            ]
        )
        state["context"] = context
    else:
        state["route"] = "rewrite_question"

    # 更新trace
    state["rag_trace"]["step"] = "grade_documents"
    state["rag_trace"]["relevant_count"] = relevant_count
    state["rag_trace"]["route"] = state["route"]

    return state


def rewrite_question_node(state: RAGstate) -> RAGstate:
    """
    查询重写节点：使用Step-back或HyDE策略改进查询
    """
    question = state["question"]

    # 第一步：决定使用哪种重写策略
    strategy_prompt = """分析以下用户问题，决定使用哪种查询重写策略来改进检索效果。

用户问题: {question}

可用策略:
1. step_back: 退一步思考，从通用概念层面提问（适合具体技术问题）
2. hyde: Hypothetical Document Embedding，生成假设的理想回答（适合需要综合信息的问题）
3. complex: 复杂策略，结合 step_back + hyde（适合复杂问题）

请选择合适的策略并解释原因。
"""

    try:
        strategy_result = strategy_llm.invoke(strategy_prompt.format(question=question))
        state["expansion_type"] = strategy_result.strategy

    except Exception as e:
        print(f"Strategy selection error: {e}")
        # 默认使用 hyde 策略
        state["expansion_type"] = "hyde"

    # 第二步：根据选择的策略执行重写
    expansion_type = state["expansion_type"]

    if expansion_type == "step_back":
        state = _apply_step_back_strategy(state, question)
    elif expansion_type == "hyde":
        state = _apply_hyde_strategy(state, question)
    elif expansion_type == "complex":
        state = _apply_complex_strategy(state, question)

    # 更新trace
    state["rag_trace"]["step"] = "rewrite_question"
    state["rag_trace"]["expansion_type"] = expansion_type
    state["rag_trace"]["expanded_query"] = state.get("expanded_query")

    return state


def _apply_step_back_strategy(state: RAGstate, question: str) -> RAGstate:
    """应用Step-back策略：退一步从通用概念层面提问"""

    step_back_prompt = """请对以下问题进行"退一步"思考。

原始问题: {question}

请:
1. 提出一个更通用的"退一步问题"，从更基础的概念层面来理解这个问题
2. 回答这个退一步问题

例如:
- 原始: "我的iPhone 13充不进电怎么办？"
- 退一步: "智能手机充电故障的常见原因有哪些？"
"""

    try:
        result = step_back_llm.invoke(step_back_prompt.format(question=question))

        state["step_back_question"] = result.step_back_question
        state["step_back_answer"] = result.step_back_answer

        # 组合成扩展查询
        state["expanded_query"] = (
            f"{question}\n\n相关背景: {result.step_back_question}\n{result.step_back_answer}"
        )

    except Exception as e:
        print(f"Step-back error: {e}")
        # 失败时使用原始问题
        state["step_back_question"] = question
        state["step_back_answer"] = ""
        state["expanded_query"] = question

    return state


def _apply_hyde_strategy(state: RAGstate, question: str) -> RAGstate:
    """应用HyDE策略：生成假设的理想回答文档"""

    hyde_prompt = """请为以下问题生成一个假设的理想回答文档。

用户问题: {question}

请生成一段文字，假设这是从知识库中找到的完美回答。这段文字应该:
1. 直接回答用户的问题
2. 包含相关的关键信息
3. 语气专业、信息完整

这个假设文档将用于帮助检索更相关的真实文档。
"""

    try:
        result = hyde_llm.invoke(hyde_prompt.format(question=question))

        state["hypothetical_doc"] = result.hypothetical_document

        # 使用假设文档作为扩展查询（用于向量检索）
        state["expanded_query"] = result.hypothetical_document

    except Exception as e:
        print(f"HyDE error: {e}")
        # 失败时使用原始问题
        state["hypothetical_doc"] = ""
        state["expanded_query"] = question

    return state


def _apply_complex_strategy(state: RAGstate, question: str) -> RAGstate:
    """应用Complex策略：结合Step-back和HyDE"""

    # 先应用step-back
    state = _apply_step_back_strategy(state, question)
    step_back_context = state.get("expanded_query", question)

    # 在step-back的基础上应用hyde
    hyde_prompt = """基于以下背景和原始问题，生成一个假设的理想回答文档。

原始问题: {question}

背景信息: {context}

请生成一段综合性的回答文档，这个文档将用于帮助检索更相关的真实文档。
"""

    try:
        result = hyde_llm.invoke(hyde_prompt.format(question=question, context=step_back_context))

        state["hypothetical_doc"] = result.hypothetical_document

        # 组合所有信息
        state["expanded_query"] = (
            f"{question}\n\n背景: {step_back_context}\n\n假设回答: {result.hypothetical_document}"
        )

    except Exception as e:
        print(f"Complex strategy error: {e}")
        # 至少保留step-back的结果
        state["expanded_query"] = step_back_context

    return state


def retrieve_expanded(state: RAGstate, use_hybrid: bool = True) -> RAGstate:
    """
    扩展检索节点：使用重写后的查询进行混合检索
    """
    expanded_query = state.get("expanded_query", state["question"])
    original_docs = state.get("graded_docs", [])

    # 生成扩展查询的稠密向量
    query_dense_embedding = embeddings.embed_query(expanded_query)

    try:
        from backend.milvus.client import get_milvus_client

        client = get_milvus_client()

        if use_hybrid:
            # 生成查询稀疏向量（BM25）
            try:
                from backend.src.sparse_embeddings import (
                    get_bm25_generator,
                    convert_to_milvus_sparse_format,
                )
                from scipy import sparse
                import numpy as np

                bm25_generator = get_bm25_generator()
                if bm25_generator.retriever is not None:
                    sparse_dict = bm25_generator.encode_query(expanded_query)
                    query_sparse_embedding = convert_to_milvus_sparse_format(sparse_dict)
                else:
                    query_sparse_embedding = sparse.csr_matrix((1, 1), dtype=np.float32)
            except Exception as e:
                print(f"BM25编码失败，回退到稠密检索: {e}")
                query_sparse_embedding = sparse.csr_matrix((1, 1), dtype=np.float32)

            # 使用混合检索
            results = client.hybrid_search(
                collection_name="document_chunks",
                query_dense_embedding=query_dense_embedding,
                query_sparse_embedding=query_sparse_embedding,
                top_k=10,  # 获取更多结果以便筛选
            )
        else:
            # 使用纯稠密检索
            results = client.search(
                collection_name="document_chunks",
                query_embedding=query_dense_embedding,
                top_k=10,
            )

        # 构建新文档列表
        new_docs = []
        for idx, result in enumerate(results):
            doc_id = result["chunk_id"]
            # 检查是否已在原始结果中
            existing = next((d for d in original_docs if d.get("id") == doc_id), None)
            if existing:
                new_docs.append(existing)
            else:
                new_docs.append(
                    {
                        "id": doc_id,
                        "content": result["content"],
                        "score": result["score"],
                        "metadata": json.loads(result.get("metadata", "{}")),
                        "source": result.get("source", ""),
                        "doc_type": result.get("doc_type", "text"),
                        "from_expanded": True,
                    }
                )

        # 合并并去重（保留原始的相关文档 + 新的检索结果）
        all_docs = []
        seen_ids = set()

        # 先加入原始的相关文档
        for doc in original_docs:
            if doc.get("is_relevant", False) and doc["id"] not in seen_ids:
                all_docs.append(doc)
                seen_ids.add(doc["id"])

        # 再加入新的文档
        for doc in new_docs:
            if doc["id"] not in seen_ids:
                all_docs.append(doc)
                seen_ids.add(doc["id"])

        # 限制总数
        all_docs = all_docs[:8]

        # 更新状态
        state["docs"] = all_docs

        # 构建最终上下文
        context = "\n\n".join(
            [f"[Document {i + 1}] {doc['content']}" for i, doc in enumerate(all_docs)]
        )
        state["context"] = context

        # 更新trace
        state["rag_trace"]["step"] = "expanded_retrieval"
        state["rag_trace"]["final_doc_count"] = len(all_docs)

    except Exception as e:
        print(f"Expanded retrieval error: {e}")
        # 出错时保留原始上下文
        if "context" not in state or not state["context"]:
            context = "\n\n".join(
                [f"[Document {i + 1}] {doc['content']}" for i, doc in enumerate(original_docs)]
            )
            state["context"] = context
        state["rag_trace"]["step"] = "expanded_retrieval"
        state["rag_trace"]["error"] = str(e)

    return state


def generate_answer_node(state: RAGstate) -> RAGstate:
    """
    生成答案节点：基于检索到的上下文生成最终回答
    """
    question = state["question"]
    context = state.get("context", "")

    answer_prompt = """基于以下检索到的信息，回答用户的问题。

检索到的信息:
{context}

用户问题: {question}

请:
1. 基于提供的上下文回答问题
2. 如果上下文不足以完整回答问题，请说明
3. 回答要准确、简洁、有帮助
"""

    try:
        response = llm.invoke(answer_prompt.format(context=context, question=question))

        state["answer"] = response.content
        state["rag_trace"]["step"] = "generate_answer"
        state["rag_trace"]["has_answer"] = True

    except Exception as e:
        print(f"Answer generation error: {e}")
        state["answer"] = "抱歉，生成回答时出现错误。"
        state["rag_trace"]["step"] = "generate_answer"
        state["rag_trace"]["error"] = str(e)

    return state


# ==================== 路由函数 ====================


def route_after_grading(state: RAGstate) -> str:
    """
    根据文档评分结果决定路由
    """
    return state.get("route", "rewrite_question")


# ==================== 构建Graph ====================


def build_rag_graph():
    """
    构建RAG工作流图
    """
    graph = StateGraph(RAGstate)

    # 添加节点
    graph.add_node("retrieve_initial", retrieve_initial)
    graph.add_node("grade_documents", grade_documents_node)
    graph.add_node("rewrite_question", rewrite_question_node)
    graph.add_node("retrieve_expanded", retrieve_expanded)
    graph.add_node("generate_answer", generate_answer_node)

    # 设置入口点
    graph.set_entry_point("retrieve_initial")

    # 添加边：初始检索 -> 文档评分
    graph.add_edge("retrieve_initial", "grade_documents")

    # 条件边：根据评分结果决定路由
    graph.add_conditional_edges(
        "grade_documents",
        route_after_grading,
        {"generate_answer": "generate_answer", "rewrite_question": "rewrite_question"},
    )

    # 添加边：重写查询 -> 扩展检索
    graph.add_edge("rewrite_question", "retrieve_expanded")

    # 添加边：扩展检索 -> 生成答案
    graph.add_edge("retrieve_expanded", "generate_answer")

    # 添加边：生成答案 -> 结束
    graph.add_edge("generate_answer", END)

    return graph.compile()


# ==================== 便捷使用函数 ====================


def run_rag(question: str) -> dict:
    """
    运行RAG流程的便捷函数

    Args:
        question: 用户问题

    Returns:
        包含答案和trace信息的字典
    """
    graph = build_rag_graph()

    initial_state = {
        "question": question,
        "query": "",
        "context": "",
        "docs": [],
        "graded_docs": [],
        "route": None,
        "expansion_type": None,
        "expanded_query": None,
        "step_back_question": None,
        "step_back_answer": None,
        "hypothetical_doc": None,
        "rag_trace": {},
    }

    result = graph.invoke(initial_state)

    return {
        "question": result["question"],
        "answer": result.get("answer", ""),
        "context": result.get("context", ""),
        "trace": result.get("rag_trace", {}),
        "route": result.get("route"),
        "expansion_type": result.get("expansion_type"),
        "docs_count": len(result.get("docs", [])),
    }


# 测试代码
if __name__ == "__main__":
    # 简单测试
    test_question = "什么是RAG技术，它如何工作？"
    print(f"测试问题: {test_question}\n")

    # 注意：实际运行需要配置好环境变量和Milvus连接
    print("RAG Graph已构建完成！")
    print("使用方法: result = run_rag('你的问题')")

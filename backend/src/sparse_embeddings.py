"""
BM25 稀疏向量生成器
用于混合检索中的关键词匹配组件
"""

from typing import List, Dict, Tuple, Optional
import bm25s
import Stemmer
import numpy as np
from scipy import sparse


class BM25SparseVectorGenerator:
    """
    BM25 稀疏向量生成器

    生成适合 Milvus SPARSE_FLOAT_VECTOR 的稀疏向量格式
    使用 bm25s 库实现高效的 BM25 评分
    """

    def __init__(self, language: str = "english", k1: float = 1.5, b: float = 0.75):
        """
        初始化 BM25 生成器

        Args:
            language: 语言代码（用于词干提取）
            k1: BM25 参数，控制词频饱和度
            b: BM25 参数，控制文档长度归一化
        """
        self.language = language
        self.k1 = k1
        self.b = b
        self.stemmer = Stemmer.Stemmer(language)
        self.retriever = None
        self.vocab_size = 0
        self.token_to_id = {}

    def fit(self, documents: List[str]) -> "BM25SparseVectorGenerator":
        """
        在文档集合上训练 BM25 模型

        Args:
            documents: 文档文本列表

        Returns:
            self
        """
        # 分词并词干提取
        corpus_tokens = bm25s.tokenize(documents, stopwords="en", stemmer=self.stemmer)

        # 创建 BM25 检索器
        self.retriever = bm25s.BM25(k1=self.k1, b=self.b)
        self.retriever.index(corpus_tokens)

        # 构建词汇表映射
        self.vocab_size = len(self.retriever.vocab_dict)
        self.token_to_id = self.retriever.vocab_dict

        print(f"BM25 模型训练完成:")
        print(f"  - 文档数: {len(documents)}")
        print(f"  - 词汇表大小: {self.vocab_size}")

        return self

    def encode_document(self, text: str) -> Dict[int, float]:
        """
        将文档编码为稀疏向量（字典格式）

        使用词频作为权重，后续通过 Milvus 的 BM25 索引计算最终分数

        Args:
            text: 文档文本

        Returns:
            稀疏向量字典 {token_id(唯一标识): weight(出现次数)}
        """
        if self.retriever is None:
            raise ValueError("BM25 模型尚未训练，请先调用 fit()")

        # 分词
        tokens = bm25s.tokenize([text], stemmer=self.stemmer, stopwords="en")
        token_ids = tokens.ids[0]
        vocab_size = len(self.retriever.vocab_dict)

        # 计算词频作为权重
        sparse_vec = {}
        for token_id in set(token_ids):
            if token_id < 0 or token_id >= vocab_size:
                continue
            # 使用词频作为权重
            freq = token_ids.count(token_id)
            if freq > 0:
                sparse_vec[int(token_id)] = float(freq)

        return sparse_vec

    def encode_query(self, text: str) -> Dict[int, float]:
        """
        将查询编码为稀疏向量（字典格式）

        Args:
            text: 查询文本

        Returns:
            稀疏向量字典 {token_id: weight}
        """
        if self.retriever is None:
            raise ValueError("BM25 模型尚未训练，请先调用 fit()")

        # 分词（查询使用二进制权重 - 存在即权重1）
        tokens = bm25s.tokenize([text], stemmer=self.stemmer, stopwords="en")
        token_ids = tokens.ids[0]

        sparse_vec = {}
        # 获取词汇表大小
        vocab_size = len(self.retriever.vocab_dict)

        for token_id in set(token_ids):
            # 忽略 OOV (Out of Vocabulary) token
            if token_id < 0 or token_id >= vocab_size:
                continue
            # 使用统一的权重1，或者可以使用词频
            sparse_vec[int(token_id)] = 1.0

        return sparse_vec

    def encode_documents_batch(self, texts: List[str]) -> List[Dict[int, float]]:
        """
        批量编码文档

        Args:
            texts: 文档文本列表

        Returns:
            稀疏向量列表
        """
        return [self.encode_document(text) for text in texts]

    def search(self, query: str, k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """
        使用 BM25 检索最相关的文档

        Args:
            query: 查询文本
            k: 返回结果数量

        Returns:
            (文档索引数组, 分数数组)
        """
        if self.retriever is None:
            raise ValueError("BM25 模型尚未训练，请先调用 fit()")

        query_tokens = bm25s.tokenize([query], stemmer=self.stemmer)
        results, scores = self.retriever.retrieve(query_tokens, k=k)

        return results[0], scores[0]


def convert_to_milvus_sparse_format(sparse_dict: Dict[int, float]):
    """
    将稀疏向量字典转换为 Milvus 接受的格式 (scipy sparse matrix)

    Milvus 2.4+ 接受的稀疏向量格式是 scipy.sparse.csr_matrix

    Args:
        sparse_dict: 稀疏向量字典 {token_id: weight}

    Returns:
        scipy.sparse.csr_matrix 格式的稀疏向量
    """
    if not sparse_dict:
        # 返回空的 csr_matrix，指定维度为1
        return sparse.csr_matrix((1, 1), dtype=np.float32)

    # 获取最大索引来确定向量维度
    max_idx = max(sparse_dict.keys())
    vector_dim = max_idx + 1

    # 构建 csr_matrix
    indices = []
    data = []
    for idx, val in sorted(sparse_dict.items()):
        if val > 0:  # 只保留非零值
            indices.append(idx)
            data.append(float(val))

    # 创建 csr_matrix (1 x vector_dim)
    row_indices = [0] * len(indices)  # 只有一行
    csr_mat = sparse.csr_matrix(
        (data, (row_indices, indices)), shape=(1, vector_dim), dtype=np.float32
    )

    return csr_mat


class HybridRetriever:
    """
    混合检索器 - 结合稠密向量和稀疏向量
    使用 RRF (Reciprocal Rank Fusion) 融合结果
    """

    def __init__(self, k: float = 60.0):
        """
        初始化混合检索器

        Args:
            k: RRF 融合参数，控制高排名文档的权重
        """
        self.k = k

    def reciprocal_rank_fusion(
        self, dense_results: List[Dict], sparse_results: List[Dict], top_k: int = 10
    ) -> List[Dict]:
        """
        使用 RRF 融合稠密和稀疏检索结果

        Args:
            dense_results: 稠密检索结果列表，每项包含 chunk_id 和其他字段
            sparse_results: 稀疏检索结果列表
            top_k: 返回结果数量

        Returns:
            融合后的结果列表
        """
        # 构建分数字典
        scores = {}
        doc_info = {}

        # 处理稠密检索结果
        for rank, doc in enumerate(dense_results):
            doc_id = doc["chunk_id"]
            # RRF 分数: 1 / (k + rank)
            rrf_score = 1.0 / (self.k + rank + 1)  # rank 从 0 开始
            scores[doc_id] = scores.get(doc_id, 0.0) + rrf_score
            # 保存文档信息
            if doc_id not in doc_info:
                doc_info[doc_id] = doc.copy()
                doc_info[doc_id]["dense_rank"] = rank + 1
                doc_info[doc_id]["dense_score"] = doc.get("score", 0.0)

        # 处理稀疏检索结果
        for rank, doc in enumerate(sparse_results):
            doc_id = doc["chunk_id"]
            rrf_score = 1.0 / (self.k + rank + 1)
            scores[doc_id] = scores.get(doc_id, 0.0) + rrf_score
            # 合并文档信息
            if doc_id not in doc_info:
                doc_info[doc_id] = doc.copy()
            doc_info[doc_id]["sparse_rank"] = rank + 1
            doc_info[doc_id]["sparse_score"] = doc.get("score", 0.0)

        # 按 RRF 分数排序
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        # 构建结果
        results = []
        for doc_id, rrf_score in sorted_docs:
            result = doc_info[doc_id].copy()
            result["rrf_score"] = rrf_score
            result["retrieval_types"] = []
            if "dense_rank" in result:
                result["retrieval_types"].append("dense")
            if "sparse_rank" in result:
                result["retrieval_types"].append("sparse")
            results.append(result)

        return results


# 全局 BM25 生成器实例
_bm25_generator: Optional[BM25SparseVectorGenerator] = None


def get_bm25_generator() -> BM25SparseVectorGenerator:
    """获取全局 BM25 生成器实例"""
    global _bm25_generator
    if _bm25_generator is None:
        _bm25_generator = BM25SparseVectorGenerator(language="english")
    return _bm25_generator


def set_bm25_generator(generator: BM25SparseVectorGenerator):
    """设置全局 BM25 生成器实例"""
    global _bm25_generator
    _bm25_generator = generator


if __name__ == "__main__":
    # 测试代码
    print("BM25 稀疏向量生成器测试")
    print("=" * 50)

    # 测试文档
    docs = [
        "The quick brown fox jumps over the lazy dog",
        "A quick brown dog outpaces a swift fox",
        "The lazy dog sleeps all day",
        "Swift foxes are known for their speed",
        "Dogs and foxes are both canines",
    ]

    # 训练模型
    bm25 = BM25SparseVectorGenerator()
    bm25.fit(docs)

    # 编码查询
    query = "quick fox"
    query_vec = bm25.encode_query(query)
    print(f"\n查询 '{query}' 的稀疏向量:")
    print(f"  非零维度数: {len(query_vec)}")
    print(f"  前5个维度: {dict(list(query_vec.items())[:5])}")

    # 编码文档
    doc_vec = bm25.encode_document(docs[0])
    print(f"\n文档 '{docs[0]}' 的稀疏向量:")
    print(f"  非零维度数: {len(doc_vec)}")
    print(f"  前5个维度: {dict(list(doc_vec.items())[:5])}")

    # 转换为 Milvus 格式
    milvus_format = convert_to_milvus_sparse_format(doc_vec)
    print(f"\nMilvus 格式:")
    print(f"  indices: {milvus_format['indices'][:10]}...")
    print(f"  values: {milvus_format['values'][:10]}...")

    # 测试检索
    print(f"\n检索 '{query}':")
    indices, scores = bm25.search(query, k=3)
    for idx, score in zip(indices, scores):
        print(f"  - Doc {idx}: {score:.4f} | {docs[idx]}")

    print("\n测试完成!")

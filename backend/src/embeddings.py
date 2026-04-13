"""DashScope Embedding wrapper for LangChain"""

import os
from typing import List, Optional
from langchain_core.embeddings import Embeddings
import requests


class DashScopeEmbeddings(Embeddings):
    """DashScope (阿里云) Embedding 模型封装

    使用 DashScope 兼容模式 API 进行文本嵌入
    文档: https://help.aliyun.com/zh/dashscope/developer-reference/text-embedding
    """

    def __init__(
        self,
        model: str = "text-embedding-v3",
        api_key: Optional[str] = None,
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
    ):
        self.model = model
        self.api_key = api_key or os.getenv("EMBEDDING_API_KEY")
        self.base_url = base_url.rstrip("/")

        if not self.api_key:
            raise ValueError("API key is required. Set EMBEDDING_API_KEY environment variable.")

    def _embed(self, texts: List[str]) -> List[List[float]]:
        """调用 DashScope API 获取 embeddings"""
        url = f"{self.base_url}/embeddings"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # 过滤空字符串，DashScope 不接受空字符串
        texts = [t if t and t.strip() else " " for t in texts]

        # DashScope API 要求 input 是字符串列表
        payload = {
            "model": self.model,
            "input": texts,  # 直接使用字符串列表，不是 {texts: [...]}
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()

            if "data" not in data or not data["data"]:
                raise ValueError(f"Invalid response from DashScope: {data}")

            # 按 index 排序 embeddings
            embeddings = sorted(data["data"], key=lambda x: x.get("index", 0))
            return [item["embedding"] for item in embeddings]

        except requests.exceptions.HTTPError as e:
            # 打印详细的错误信息
            print(f"[ERROR] DashScope API 请求失败")
            print(f"  URL: {url}")
            print(f"  Model: {self.model}")
            print(f"  Texts count: {len(texts)}")
            print(f"  First text length: {len(texts[0]) if texts else 0}")
            try:
                error_detail = response.json()
                print(f"  Response: {error_detail}")
            except:
                print(f"  Response text: {response.text}")
            raise ValueError(f"DashScope API request failed: {e}")

        except requests.exceptions.RequestException as e:
            raise ValueError(f"DashScope API request failed: {e}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents

        Args:
            texts: 要嵌入的文本列表

        Returns:
            嵌入向量列表
        """
        if not texts:
            return []

        # DashScope 每次最多支持 10 条，需要分批处理
        batch_size = 10
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            embeddings = self._embed(batch)
            all_embeddings.extend(embeddings)

        return all_embeddings

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query

        Args:
            text: 要嵌入的查询文本

        Returns:
            嵌入向量
        """
        if not text:
            text = " "
        embeddings = self._embed([text])
        return embeddings[0]

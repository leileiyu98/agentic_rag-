"""Text Splitter - 智能文本分块策略"""

import re
from typing import List, Optional, Callable
from dataclasses import dataclass
import hashlib


@dataclass
class TextChunk:
    """文本块数据类"""

    content: str
    index: int  # 块索引
    start_pos: int  # 在原文档中的起始位置
    end_pos: int  # 在原文档中的结束位置
    metadata: dict  # 元数据
    chunk_id: str  # 唯一标识


class RecursiveCharacterTextSplitter:
    """
    递归字符文本分块器

    按优先级尝试不同的分隔符进行分割：
    1. 段落分隔符 (\n\n)
    2. 换行符 (\n)
    3. 句子分隔符 (.!?)
    4. 单词边界 (空格)
    5. 字符

    优先保持语义完整性
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", "。", "；", "!", "?", ".", ";", " ", ""]

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None,
        length_function: Callable[[str], int] = len,
        keep_separator: bool = True,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or self.DEFAULT_SEPARATORS
        self.length_function = length_function
        self.keep_separator = keep_separator

    def split_text(self, text: str, doc_metadata: dict = None) -> List[TextChunk]:
        """分割文本为块"""
        doc_metadata = doc_metadata or {}

        # 先按分隔符分割
        chunks = self._split_by_separators(text)

        # 合并到目标大小
        merged = self._merge_chunks(chunks)

        # 创建 TextChunk 对象
        result = []
        current_pos = 0

        for i, content in enumerate(merged):
            chunk = TextChunk(
                content=content,
                index=i,
                start_pos=current_pos,
                end_pos=current_pos + len(content),
                metadata=doc_metadata.copy(),
                chunk_id=self._generate_chunk_id(content, i),
            )
            result.append(chunk)
            current_pos += len(content)

            # 减去重叠部分
            if i < len(merged) - 1 and self.chunk_overlap > 0:
                current_pos = max(0, current_pos - self.chunk_overlap)

        return result

    def _split_by_separators(self, text: str) -> List[str]:
        """使用分隔符分割文本"""
        # 使用第一个分隔符（通常是段落）
        separator = self.separators[0] if self.separators else "\n\n"

        if separator == "":
            return [c for c in text if c.strip()]

        parts = text.split(separator)
        return [p.strip() for p in parts if p.strip()]

    def _merge_chunks(self, chunks: List[str]) -> List[str]:
        """将小块合并到目标大小"""
        if not chunks:
            return []

        result = []
        current_chunk = []
        current_size = 0

        for chunk in chunks:
            chunk_size = self.length_function(chunk)

            # 单个块就超过限制，需要强制分割
            if chunk_size > self.chunk_size:
                # 先保存当前累积的块
                if current_chunk:
                    result.append(" ".join(current_chunk))
                    current_chunk = []
                    current_size = 0

                # 强制分割大块
                result.extend(self._force_split(chunk))
                continue

            # 如果加上当前块会超过限制，先保存
            if current_chunk and current_size + chunk_size > self.chunk_size:
                result.append(" ".join(current_chunk))
                # 保留重叠
                current_chunk = self._get_overlap_chunks(current_chunk)
                current_size = sum(self.length_function(c) for c in current_chunk)

            current_chunk.append(chunk)
            current_size += chunk_size

        # 处理最后一个块
        if current_chunk:
            result.append(" ".join(current_chunk))

        return result

    def _force_split(self, text: str) -> List[str]:
        """强制将文本分割到目标大小"""
        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            chunk = text[start:end]
            chunks.append(chunk)

            # 下一步起始位置（考虑重叠）
            start = end - self.chunk_overlap if end < text_len else end

        return chunks

    def _get_overlap_chunks(self, chunks: List[str]) -> List[str]:
        """获取用于重叠的块"""
        overlap_size = 0
        overlap_chunks = []

        for chunk in reversed(chunks):
            chunk_size = self.length_function(chunk)
            if overlap_size + chunk_size <= self.chunk_overlap:
                overlap_chunks.insert(0, chunk)
                overlap_size += chunk_size
            else:
                break

        return overlap_chunks

    def _generate_chunk_id(self, content: str, index: int) -> str:
        """生成块的唯一ID"""
        hash_input = f"{content[:100]}:{index}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:16]


class MarkdownTextSplitter(RecursiveCharacterTextSplitter):
    """Markdown 专用分块器

    优先按 Markdown 标题分割，保持文档结构
    """

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, **kwargs):
        # Markdown 分隔符：标题优先
        separators = [
            "\n## ",  # H2
            "\n### ",  # H3
            "\n#### ",  # H4
            "\n\n",  # 段落
            "\n",  # 换行
            "。",
            "；",
            "!",
            "?",
            ".",
            ";",
            " ",
            "",
        ]
        super().__init__(chunk_size, chunk_overlap, separators, **kwargs)

    def split_text(self, text: str, doc_metadata: dict = None) -> List[TextChunk]:
        """分割Markdown文本，提取标题作为元数据"""
        doc_metadata = doc_metadata or {}

        # 提取所有标题
        headers = self._extract_headers(text)

        chunks = super().split_text(text, doc_metadata)

        # 为每个块添加最近的标题信息
        for chunk in chunks:
            chunk.metadata["headers"] = self._get_headers_for_position(
                headers, chunk.start_pos
            )

        return chunks

    def _extract_headers(self, text: str) -> List[tuple]:
        """提取所有标题及其位置"""
        headers = []
        pattern = r"^(#{1,6})\s+(.+)$"

        for match in re.finditer(pattern, text, re.MULTILINE):
            level = len(match.group(1))
            title = match.group(2).strip()
            pos = match.start()
            headers.append((pos, level, title))

        return headers

    def _get_headers_for_position(self, headers: List[tuple], pos: int) -> dict:
        """获取指定位置的标题层级"""
        current_headers = {}

        for h_pos, level, title in headers:
            if h_pos <= pos:
                current_headers[f"h{level}"] = title
            else:
                break

        return current_headers


class CodeTextSplitter(RecursiveCharacterTextSplitter):
    """代码专用分块器

    按代码结构分割：类、函数、代码块
    """

    def __init__(
        self,
        chunk_size: int = 1500,
        chunk_overlap: int = 300,
        language: str = "python",
        **kwargs,
    ):
        self.language = language

        # 根据语言选择分隔符
        separators = self._get_separators_for_language(language)
        super().__init__(chunk_size, chunk_overlap, separators, **kwargs)

    def _get_separators_for_language(self, language: str) -> List[str]:
        """获取语言特定的分隔符"""
        separators_map = {
            "python": ["\nclass ", "\ndef ", "\n\n", "\n", " ", ""],
            "javascript": [
                "\nclass ",
                "\nfunction ",
                "\nconst ",
                "\nlet ",
                "\nvar ",
                "\n\n",
                "\n",
                " ",
                "",
            ],
            "java": [
                "\npublic class ",
                "\nprivate class ",
                "\nprotected class ",
                "\npublic void ",
                "\n\n",
                "\n",
                " ",
                "",
            ],
            "go": ["\nfunc ", "\ntype ", "\nconst ", "\nvar ", "\n\n", "\n", " ", ""],
            "rust": [
                "\nfn ",
                "\nstruct ",
                "\nimpl ",
                "\nconst ",
                "\nlet ",
                "\n\n",
                "\n",
                " ",
                "",
            ],
        }
        return separators_map.get(language, ["\n\n", "\n", " ", ""])


def get_splitter_for_document(
    doc_type: str, **kwargs
) -> RecursiveCharacterTextSplitter:
    """根据文档类型获取合适的分块器"""

    splitters = {
        "markdown": MarkdownTextSplitter,
        "pdf": RecursiveCharacterTextSplitter,
        "word": RecursiveCharacterTextSplitter,
        "text": RecursiveCharacterTextSplitter,
        "code": CodeTextSplitter,
    }

    splitter_class = splitters.get(doc_type, RecursiveCharacterTextSplitter)
    return splitter_class(**kwargs)


# 测试代码
if __name__ == "__main__":
    # 测试文本
    test_text = """
这是第一段文字。它包含了一些内容。

这是第二段文字。它也有内容。
这是第二段的继续。

这是第三段文字。更多内容在这里。
"""

    print("文本分块器测试")
    print("=" * 50)

    splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=10)
    chunks = splitter.split_text(test_text)

    print(f"原始文本长度: {len(test_text)}")
    print(f"分割成 {len(chunks)} 个块\n")

    for chunk in chunks:
        print(f"块 {chunk.index}: {len(chunk.content)} 字符")
        print(f"  ID: {chunk.chunk_id}")
        print(f"  内容: {chunk.content[:50]}...")
        print()
